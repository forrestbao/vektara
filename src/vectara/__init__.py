# A Python SDK and CLI for Vectara's RAG platform
# GPL v3.0 License
# Not officially endorsed by Vectara
# Use at your own risk

# Copyleft 2023 Forrest Sheng Bao
# forrest@vectara.com

import json, os, io
from typing import List, Literal, Dict

import requests

import dotenv

from tqdm import tqdm
from IPython.display import Markdown, display_markdown
import markdown, bs4
import textwrap

from funix import funix_class, funix_method, funix
from funix.session import set_global_variable
from funix.hint import BytesFile
from typing import Literal

import sqlite3
con = sqlite3.connect("feedback.db", check_same_thread=False)
cursor = con.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    corpus_id INTEGER NOT NULL,
    top_k INTEGER NOT NULL,
    lang TEXT NOT NULL,
    score REAL NOT NULL,
    raw_response TEXT NOT NULL,
    consistent BOOLEAN NOT NULL
);
""")
con.commit()

vectara_config = ".vectara_config"

@funix(disable=True)
def md2text(md: str):
    html = markdown.markdown(md)
    soup = bs4.BeautifulSoup(html, features='html.parser')
    return soup.get_text()

@funix_class()
class vectara():
    @funix_method(
        title="Initialize Vectara",
        print_to_web=True,
        widgets= { # api_key and client_secret must be str to be compatible with Google Fire.
                   # If using Funix only, we can set them to ipywidgets.password
            'api_key': 'password',
            'client_secret': 'password',
        },
        conditional_visible=[
            {
                "when": {
                    "use_oauth2": True
                },
                "show": ["client_id", "client_secret"]
            },
            {
                "when": {
                    "use_oauth2": False
                },
                "show": ["api_key"]
            }
        ]
    )
    def __init__(self, 
                base_url: str = "https://api.vectara.io", 
                customer_id: str = None,
                api_key: str = None, 
                client_id: str = None, 
                client_secret: str = None, 
                from_cli: bool = False, 
                use_oauth2: bool = False
            ):
        def get_env(env: str, default: str) -> str:
            result = os.environ.get(env, default)
            if result is None or result.isspace() or len(result) == 0:
                raise TypeError(f"Expecting `{env}` in __init__ of the `vectara` class or as an environment variable. But it is not set.")
            return result

        def is_void(s: str):
            return s is None or s.isspace() or len(s) == 0

        def str2bool(value: str) -> bool:
            return value.lower() in ['true', 'yes', '1']

        self.proxy_mode = str2bool(os.environ.get('VECTARA_PROXY_MODE', 'false'))
        # only for LlamaKey.ai to use. 

        if base_url != "https://api.vectara.io":
            self.proxy_mode = True # force proxy mode if base_url is not the default

        self.base_url = get_env('VECTARA_BASE_URL', base_url)  # must 
        self.customer_id = get_env('VECTARA_CUSTOMER_ID', customer_id)  # must 
        client_id = os.environ.get('VECTARA_CLIENT_ID', client_id)
        client_secret = os.environ.get('VECTARA_CLIENT_SECRET', client_secret)
        self.from_cli = from_cli

        self.client_id = None 
        self.client_secret = None
        self.api_key = None 
        self.jwt_token = None

        api_key = os.environ.get('VECTARA_API_KEY', api_key)

        if use_oauth2 or is_void(api_key): # manually request to use OAuth2 or API Key is not available
            if use_oauth2:
                print ("You chose to use OAuth2. API Key will be ingored.")
            if is_void(api_key): 
                print ("API Key not set. Fall back to OAuth2 for authentication.")
            assert not is_void(client_id), "OAuth2 client_id not available. Please set."
            assert not is_void(client_secret), "OAuth2 client_secret not available. Please set."
            self.client_id = client_id
            self.client_secret = client_secret
            self.acquire_jwt_token()
        else: # API key is available
            self.api_key = api_key 
            if not is_void(client_id) and not is_void(client_secret):
                print ("Although OAuth2 credentials are available, API key will be used because it is present. To use OAuth2, either unset API key or set use_oauth2 to True to override.")
               
        if not from_cli:
            print("Vectara SDK initialized. ")

        # FIXME: CLI mode cannot maintain the instance variable self.jwt_token set in non-__init__ methods, so we need to get a new JWT token for each method call.
        # But this seems to be a limitation of Google-Fire that a member variable cannot be set in one method (except the __init__) and used in another method.

        # FIXME: Load JWT_Token from dotenv if in CLI mode.
        # If jwt_token is not set in a dotenv file, generate one
        # if from_cli: # only needed for command line interface
        #     print ("CLI mode. ")
        #     if dotenv.dotenv_values(vectara_config).get("VECTARA_JWT_TOKEN", "") == "":
        #         self.acquire_jwt_token()
        #         print ("JWT_Token set in CLI mode", self.jwt_token)
        #         dotenv.set_key(vectara_config, "VECTARA_JWT_TOKEN", self.jwt_token)
        
        # question, corpus_id, top_k, lang, score, raw_return
        
        self.last_result: dict = {}

    @funix_method(disable=True)
    def acquire_jwt_token(self):
        """Acquire a JWT token. It will expire in 30 minutes.

        No arguments needed.

        """
        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }


        if self.proxy_mode:
            url = f"{self.base_url}/oauth2/token"
        else:
            url = f"https://vectara-prod-{self.customer_id}.auth.us-west-2.amazoncognito.com/oauth2/token"

        response = requests.post(
            url,
            data=payload,
            headers=headers)

        try: 
            jwt_token = response.json()["access_token"]
        except:
            print("Failed to acquire JWT token. ")
            print(response.json())
            exit() # exit the program if failed to acquire JWT token

        if not self.from_cli:
            print(
                "Bearer/JWT token generated. It will expire in 30 minutes. To-regenerate, please call acquire_jwt_token(). ")

        self.jwt_token = jwt_token

        if self.from_cli:
            dotenv.set_key(vectara_config, "VECTARA_JWT_TOKEN", jwt_token)

        return jwt_token

    @funix_method(title="Create corpus", print_to_web=True)
    def create_corpus(self, corpus_name: str, corpus_description: str = "") -> int | None:
        """Create a corpus given the corpus_name and corpus_description

        params:
            corpus_name: the name given to a corpus
            corpus_description: the descrption to a corpus
        """
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/create-corpus"

        payload = json.dumps(
            {
                "corpus": {
                    "name": corpus_name,
                    "description": corpus_description
                }
            }
        )

        headers = {
            "customer-id": self.customer_id,
            # Customer ID must be there. Otherwise, error-16, "Request does not contain customer-id-bin header."
        }
        
        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            corpus_id = response.json()['corpusId']
            print("New corpus created, corpus ID is:", corpus_id)
            print("Please write down this corpus ID. You will need it to upload files to it and to query against it.")
            return corpus_id
        else:
            print("Corpus creation failed. ")
            print(response.json())
            return None

    @funix_method(title="Reset corpus", print_to_web=True)
    def reset_corpus(self, corpus_id: int):
        """Create a corpus given the corpus_name and corpus_description

        params:
            corpus_id: the ID of the corpus to reset
        """
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/reset-corpus"

        payload = json.dumps(
            {
                "corpusId": corpus_id
            }
        )

        headers = {
            "customer-id": self.customer_id,
            # Customer ID must be there. Otherwise, error-16, "Request does not contain customer-id-bin header."
        }
        
        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            print(f"Resetting corpus {corpus_id} successful. ")
        else:
            print(f"Failed resetting corpus {corpus_id}. ")

        return None

    @funix_method(disable=True)
    def upload(self, 
            corpus_id: int, 
            source: str | List[str], 
            doc_id: str | List[str] = None, 
            metadata: Dict | List[Dict]= {}, 
            verbose: bool = False
        ) -> str | List[str] :
        """Upload a file, a list of files, or files in a folder, to a corpus specified by corpus_id

        params:
            corpus_id: the corpus ID to upload to
            source: the source to upload, a file path, a folder path, or a list of file paths
            metadata: metadata for file(s). If a dict, then the same metadata will be used for all files in the request. If a list of dict, then each element is the metadata for each file in the request.
            doc_id: alphanumeric ID(s) for referring to the document(s) later. If a string, then it only works when source is a single file. If a list of strings, then each element of `doc_id` is the `doc.id` for each file in the request.
        """
        if isinstance(source, str):
            if os.path.isfile(source):
                assert doc_id is None or isinstance(doc_id, str), "doc_id must be either empty or a string if source is a single file."
                r = self.upload_file(corpus_id, source, doc_id=doc_id, metadata=metadata, verbose=True)
            elif os.path.isdir(source):
                # FIXME: default descrptions for upload_folder() is an empty list. Diff from the default description for upload()).
                assert doc_id is None or isinstance(doc_id, list), "doc_id must be a list if source is a folder."
                r = self.upload_folder(corpus_id, source, doc_ids=doc_id, metadata=metadata, verbose=verbose)
            else:
                print("Invalid source. ")
        elif isinstance(source, list):
            # FIXME: default descrptions for upload_files() is an empty list. Diff from the default description for upload()).
            assert doc_id is None or isinstance(doc_id, list), "doc_id must be either empty or a list if source is a list of file paths."
            r = self.upload_files(corpus_id, source, doc_ids=doc_id, metadata=metadata, verbose=verbose)
        else:
            print(f"Invalid source {source} ")
            exit() 
        return r

    @funix_method(title="Upload file")
    def upload_file_from_funix(self, corpus_id: int, filebuf: BytesFile, doc_id: str = "", metadata:str = "", verbose: bool = False) -> Markdown:
        """Drag and drop a file to Funix frontend to add it to a corpus specified by corpus_id
        """
        url = f"{self.base_url}/v1/upload?c={self.customer_id}&o={corpus_id}"

        if doc_id == "":
            doc_id = "A file uploaded via Funix"

        file_payload = {
            "file": (doc_id, io.BytesIO(filebuf), 'application/octet-stream'), 
            "doc_metadata": (None, json.dumps(metadata), 'application/json')
        }
       
        headers = {}
        
        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        print(f"Uploading file **{doc_id}** to corpus **{corpus_id}**...")

        response = requests.post(
            url,
            headers=headers,
            files=[file_payload]
        )

        if response.status_code == 200:
            if verbose:
                return "### **Success.** " + f"```{response.json()}```" 
            else: 
                return "### **Success.** "
        else:
            return "### **Success.** " + f"```{response.json()}```" 

    @funix_method(disable=True)
    def upload_file(self, corpus_id: int, filepath: str, doc_id: str = "", metadata: Dict = {}, verbose: bool = False):
        """Upload a file from local storage to a corpus specified by corpus_id

        params:
            corpus_id: the corpus ID to upload to
            filepath: path to file
            doc_id: a alphanumeric ID for referring to the document later
        """
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/upload?c={self.customer_id}&o={corpus_id}"

        if doc_id == None or doc_id == "":
            doc_id = os.path.basename(filepath)

        file_payload = {
            "file": (doc_id, open(filepath, 'rb'), 'application/octet-stream'), 
            "doc_metadata": (None, json.dumps(metadata), 'application/json')
        }

        headers = {}

        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        if verbose:
            print(f"Uploading...{filepath}", end=" ")

        response = requests.post(
            url,
            headers=headers,
            files=file_payload
        )

        if response.status_code == 200:
            print("Success. ")
        else:
            print("Failed. ")
            print(response.json())

        return response.json() 

    @funix_method(disable=True)
    def upload_files(self, corpus_id, filepaths: List[str], doc_ids: List[str] = [], metadata: Dict | List[Dict] = {}, verbose: bool = False) -> List[Dict]:
        """Upload a list of files from local storage

        params:
            filepaths: paths to files
            doc_ids: alphanumeric IDs for referring to the documents later
            metadata: metadata for files. If a dict, then the same metadata will be used for all files in the request. If a list of dict, then each element is the metadata for each file in the request.
        """

        assert len(filepaths) == len(set(filepaths)), "Duplicate filepaths found in `filepaths`. Please make sure all filepaths are unique. "

        if doc_ids == [] or doc_ids == None:
            print ("doc_ids is empty. Using filenames as doc_ids.")
            doc_ids = [os.path.basename(file) for file in filepaths]
        else:
            assert len(doc_ids) == len(filepaths), "Length of doc_ids must be the same as the number of files."

        if isinstance(metadata, dict):
            print ("metadata is a dict. Duplicating it for all files.")
            metadata = [metadata] * len(filepaths)
        else: 
            assert len(metadata) == len(filepaths), "Length of metadata must be the same as the number of files."        

        responses = [] 
        for doc_id, metadata, filepath in (
                pbar := tqdm(zip(doc_ids, metadata, filepaths), 
                total=len(filepaths), 
                desc="Uploading...")):
            pbar.set_postfix_str(filepath)
            response = self.upload_file(corpus_id, filepath, doc_id=doc_id, metadata=metadata, verbose=verbose)
            responses.append(response)

        return responses
    
    @funix_method(disable=True)
    def upload_folder(self, corpus_id: str, dirpath: str, doc_ids: List[str] = [], metadata: Dict | List[Dict] = {}, verbose: bool = False) -> List[Dict]:
        """Upload all files from a directory

        params:
            filepaths: paths to files
            doc_ids: alphanumeric IDs for referring to the documents later
            metadata: metadata for files. If a dict, then the same metadata will be used for all files in the request. If a list of dict, then each element is the metadata for each file in the request.
        """

        print("Uploading files from folder:", dirpath)
        files = [os.path.join(dirpath, file) for file in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, file))]

        responses = []
        response = self.upload_files(corpus_id, files, doc_ids=doc_ids, metadata=metadata, verbose=verbose)
        responses.append(response)
        return responses

    @funix_method(disable=True)
    def query(self,
              corpus_id: int,
              query: str,
              top_k: int = 5,
              lang: str = 'auto',
              contextConfig: dict = None,
              return_summary: bool = True,
              metadata_filter: str = "", 
              print_format: Literal['json', 'markdown'] = 'markdown',
              verbose: bool = False
        ) -> Dict:
        """Make a query to a corpus at Vectara

        params:
            corpus_id: the corpus ID to send the query to
            query: the query (question, search terms) to ask
            top_k: the number of most matching results to return and to summarize
            lang: the language in which a summary is generated
            contextConfig: See https://docs.vectara.com/docs/rest-api/query? for details 
            return_summary: whether to return a summary of the top_k results
            metadata_filter: a dictionary of metadata filter to narrow down the search results. See https://docs.vectara.com/docs/learn/metadata-search-filtering/filter-overview and for details. 
        """
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/query"
        payload = {
                "query": [
                    {
                        "query": query,
                        "numResults": top_k,
                        "corpusKey": [
                            {
                                # "customerId": customer_id,
                                "corpusId": corpus_id,
                            }
                        ]
                    }
                ]
            }

        if contextConfig is not None: # add context 
            payload["query"][0]["contextConfig"] = contextConfig

        if return_summary: # add summary 
            payload["query"][0]["summary"] = [
                {
                    'maxSummarizedResults': top_k,
                    'responseLang': lang, 
                    'factualConsistencyScore': True 
                }
            ] 

        if metadata_filter != "": # add metadata filter
            payload["query"][0]["corpusKey"][0]["metadataFilter"] = metadata_filter

        payload = json.dumps(payload)

        headers = {
            # 'Content-Type': 'application/json',
            # 'Accept': 'application/json',
            'customer-id': self.customer_id,
        }
        
        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        response = requests.post(url, headers=headers, data=payload)

        print (response.json()) 

        if response.status_code != 200:
            print(f"Vectara server returned {response.status_code} error. ")
            print(json.dumps(response.json(), indent=2))
            return {}
        else:
            print("Query successful. ")
            self.last_result = {
                "question": query,
                "corpus_id": corpus_id,
                "top_k": top_k,
                "lang": lang,
                "factualConsistencyScore": response.json()['responseSet'][0]['summary'][0]['factualConsistency']['score'] if return_summary else None,
                "raw_response": response.json(),
            }
            if self.from_cli or verbose:
                simple_json = post_process_query_result(response.json(), format=print_format)
                print(simple_json)
            else:
                return response.json()

    @funix_method(title="Query", keep_last = True)
    def query_funix(self, corpus_id: int,
                    query: str,
                    top_k: int = 5,
                    lang: str = 'auto') -> Markdown:
        result = post_process_query_result(self.query(corpus_id, query, top_k, lang))
        set_global_variable("last_markdown_result", "\n".join(result.splitlines()[:-3]))
        return result
    
    @funix_method(
        title="Feedback",
        session_description="last_markdown_result",
    )
    def feedback(self, consistent: Literal["Yes", "No"]) -> str:
        if not self.last_result:
            return "No query result to provide feedback for."
        is_consistent = True if consistent == "Yes" else False
        cursor.execute("""
        INSERT INTO feedback (question, corpus_id, top_k, lang, score, raw_response, consistent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.last_result['question'],
            self.last_result['corpus_id'],
            self.last_result['top_k'],
            self.last_result['lang'],
            self.last_result['score'],
            json.dumps(self.last_result['raw_response'], ensure_ascii=False),
            is_consistent
        ))
        con.commit()
        set_global_variable("last_markdown_result", "")
        self.last_result = {}
        return "Thank you for your feedback."

    @funix(disable=True)
    def upload_chunk(self, 
            corpus_id: int,
            chunks: List[str],
            doc_id: str = "",
            metadata: Dict = {},
            verbose: bool = False):
        """Upload chunks of text to a corpus specified by corpus_id.
        All chunks share the same doc_id and metadata.
        """
        url = "https://api.vectara.io/v1/core/index"

        parts = [{"text": chunk} for chunk in chunks]
        document = {'document_id': doc_id, 'parts': parts, 'metadataJson': json.dumps(metadata)} 
        request = {'customer_id': self.customer_id, 'corpus_id': corpus_id, 'document': document}

        headers = {}
            
        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        print ("Uploading the chunks...")

        response = requests.post(
            url,
            headers=headers, 
            data=json.dumps(request) 
            )

        if verbose:
            print (response.json()) 

        return response.json()

@funix(disable=True)
def post_process_query_result(
    query_result: Dict,
    format: Literal['json', 'markdown'] = 'markdown',
    jupyter_display: bool = False, 
    collect_feedback: bool = False) -> Markdown | str:
    """Postprocess query results in Vectara's JSON into a simpler dictionary and a Markdown string for displaying

    jupyter_display: whether to display the result in a Jupyter notebook. Useful if using in Jupyter notebooks.
    """

    # TODO: Extract title from metadata for each document.

    md = ""

    answers = query_result['responseSet'][0] # Since we only make one query each time, there is only one element in the responseSet

    try: 
        summary = answers['summary'][0]['text']
        factualConsistencyScore = answers['summary'][0]['factualConsistency']['score']
    except IndexError:
        summary = "No summary available."
        factualConsistencyScore = "N/A"

    summary_md = '\n'.join(textwrap.wrap(summary, 100))
    md += f"""\
### Here is the answer
{summary_md if format == 'markdown' else summary}

Factual Consistency Score: `{factualConsistencyScore}`

### References:
    """

    simple_result = {'summary': {'text': summary, 'factualConsistencyScore': factualConsistencyScore}, 'references': []}

    for number, answer in enumerate(answers['response']):
        src_doc_index = answer['documentIndex']
        src_doc_id = answers['document'][src_doc_index]['id']
        matchness = answer['score']

        simple_result['references'].append(
            {
                'doc_index': src_doc_index,
                'doc_id': src_doc_id,
                'text': answer['text'], 
                "matchness": matchness
            }
        )

        md += \
f"""
{number+1}. From document **{src_doc_id}** (matchness={matchness}):
  _...{md2text(answer['text'])}..._
"""
    
    if collect_feedback:
        md += "\n\n[Feedback](/feedback)"

    format = format.lower()

    if format == 'markdown':
        if jupyter_display:
            md_obj = Markdown(md)
            display_markdown(md_obj)
        return md
    elif format == 'json':
        # md = '```json\n' + json.dumps(simple_result, indent=2) + "\n```"
        md = json.dumps(simple_result, indent=2)
        if jupyter_display:
            display_markdown(Markdown(f"```json\n{md}\n```"))
        return md
