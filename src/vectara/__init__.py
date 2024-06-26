# A Python SDK and CLI for Vectara's RAG platform
# GPL v3.0 License
# Not officially endorsed by Vectara
# Use at your own risk

# Copyleft 2023 Forrest Sheng Bao et al.
# forrest@vectara.com


import json, os, io, time
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
        """Initialize a ``vectara``-class object.

        This function supports authentication with Vectara server using either OAuth2 or API Key. If using OAuth2, ``client_id`` and ``client_secret`` must be provided. If using API Key, ``api_key`` must be provided. When both OAuth2 and API credentials are provided, API Key will be used.

        Following the convention set by OpenAI's API in the GenAI era, the credentials will default to those in the environment variables of the operating system.

        Examples
        ------------
        >>> import vectara
        >>> client = vectara.vectara() # get default credentials from environment variables
        >>> client = vectara.vectara(api_key='abc', customer_id='123') # pass in credentials for using Personal API key
        >>> client = vectara(client_id='abc', client_secret='xyz', customer_id='123') # pass in credentials for using OAuth2

        Parameters
        --------------
        base_url: str
            The base URL of the Vectara API. Default is ``https://api.vectara.io``. It can be an URL provided by an API proxy, such as one from `LlamaKey.ai <LlamaKey.ai>`_.
        customer_id: str
            The customer ID of the Vectara account. Default to environment variable ``VECTARR_CUSTOMER_ID``. To get an Vectara customer ID, see `here <https://docs.vectara.com/docs/quickstart#view-your-customer-id>`_.
        api_key: str
            The API key of the Vectara account. Default to environment variable ``VECTARA_API_KEY``. To get a Vectara API key, see `here <https://docs.vectara.com/docs/api-reference/auth-apis/api-keys>`_.
        client_id: str
            The client ID for OAuth2 authentication. Default to environment variable ``VECTARA_CLIENT_ID``. To get an OAuth2 client ID, follow the instructions `here <https://docs.vectara.com/docs/console-ui/app-clients>`_ or `here <https://docs.vectara.com/docs/learn/authentication/oauth-2>`_.
        client_secret: str
            The client secret for OAuth2 authentication. Default to environment variable ``VECTARA_CLIENT_SECRET``. To get an OAuth2 client secret, follow the instructions `here <https://docs.vectara.com/docs/console-ui/app-clients>`_ or `here <https://docs.vectara.com/docs/learn/authentication/oauth-2>`_.
        from_cli: bool
            Whether the initialization is from a command line interface. If True, the initialization will be silent and the JWT token will be saved in a dotenv file. Default: False.
        use_oauth2: bool
            Whether to use OAuth2 for authentication. If True, the client_id and client_secret must be provided. If False, the api_key must be provided. Default: False.

        """
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
        """Acquire/renew a JWT token. For OAuth2 only. The JWT token expires after 30 minutes. If you use OAuth2, you need to call this method every 30 minutes to get a new JWT token.

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
    def create_corpus(self, corpus_name: str, corpus_description: str = "") -> int | dict:
        """Create a corpus, given a ``corpus_name`` and an optional ``corpus_description``.

        Examples
        ------------
        >>> corpus_id = client.create_corpus('America, the Beautiful') # create a new corpus called 'America, the Beautiful'

        Parameters
        ------------
            corpus_name: str
                The name of the corpus being created.
            corpus_description: str
                (Optional) The descrption to a corpus.

        Returns
        ---------
            int | dict
                The ID of the newly created corpus. If the creation fails, return the  response as a nested Python dict for further inspection.

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
            return response.json()

    @funix_method(title="Reset corpus", print_to_web=True)
    def reset_corpus(self, corpus_id: int) -> int | dict:
        """Reset a corpus specified by ``corpus_id``.

        Examples
        ------------
        >>> import vectara
        >>> client = vectara.vectara() # get default credentials from environment variables
        >>> client.reset_corpus(11) # reset the corpus with ID 11

        Parameters
        ------------
            corpus_id: int
                the ID of the corpus to reset

        Returns
        ---------
            int | str
                1 if the reset is successful. Else, the response as a nested Python dict for further inspection.

        References
        ------------
            https://docs.vectara.com/docs/rest-api/reset-corpus

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
            return 1
        else:
            print(f"Failed resetting corpus {corpus_id}. ")
            return response.json()

    def list_documents(self,
            corpus_id: int,
            numResults: int = 10,
            pageKey: str | None = None
        ) -> dict:
        """List documents in a corpus specified by ``corpus_id`` up to the number of the optional parameter ``numResults``.

        Examples
        ------------
        >>> import vectara
        >>> client = vectara.vectara() # get default credentials from environment variables
        >>> client.list_documents(11, numResults=5) # list the first 5 documents in the corpus with ID 11

        Parameters
        ------------
            corpus_id: int
                the ID of the corpus to list documents from
            numResults: int
                the number of documents to list. The max value is 1,000.  Default is 10.
            pageKey: str
                (Optional) the page key to get the next page of results. Default is None.

        Returns
        ---------
            dict
                A nested Python dict containing the list of documents in the corpus.

        References
        ------------
            https://docs.vectara.com/docs/rest-api/list-documents

        """
        url = f"{self.base_url}/v1/list-documents"

        headers = {}

        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        payload = {
            "corpusId": corpus_id,
            "numResults": numResults
        }

        if pageKey:
            payload["pageKey"] = pageKey

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload)
            )

        return response.json()

    @funix_method(disable=True)
    def upload(self,
            corpus_id: int,
            source: str | List[str],
            doc_id: str | List[str] = None,
            metadata: Dict | List[Dict]= {},
            verbose: bool = False
        ) -> dict | List[dict]:
        """Upload a file, a list of files, or files in a folder, to a corpus specified by ``corpus_id``

        Examples
        ------------
        >>> client = vectara.vectara() # get default credentials from environment variables
        >>> client.upload(corpus_id, 'test_data/consitution_united_states.txt') # upload one file
        >>> client.upload(corpus_id, ['test_data/consitution_united_states.txt', 'test_data/declaration_of_independence.txt'])  # upload a list of files
        >>> client.upload(corpus_id, "test_data") # upload all files in a folder, no recursion
        >>> client.upload(
                corpus_id = 11,
                source = 'test_data/consitution_united_states.txt',
                doc_id='we the people',
                metadata={
                    'number of amendements': '27',
                    'Author': 'Representatives from 13 states',
                    'number of words': 4543
                    },
                verbose=True
            )
        >>> client.upload(
                corpus_id = 11,
                source = ['test_data/consitution_united_states.txt', 'test_data/declaration_of_independence.txt', 'test_data/gettysburg_address.txt'],
                doc_id=[
                    'the rights',
                    'the beginning',
                    'the war'
                ],
                metadata=[
                    {'Last update': 'May 5, 1992', 'Author': "U.S. Congress"},
                    {'Location': 'Philadelphia, PA', 'Author': "Thomas Jefferson et al."}, # Declaration of Independence
                    {'Location': 'Gettysburg, PA', 'Author': 'Abraham Lincoln', 'Date': 'November 19, 1863'} # Gettysburg Address
                ]
            )

        Parameters
        ------------
            corpus_id: int
                the corpus ID to upload to
            source: str | List[str]
                the source to upload, a file path, a folder path, or a list of file paths
            doc_id: str or list of str
                (Optional) alphanumeric ID(s) for referring to the document(s) later. If a string, then it only works when source is a single file. If a list of strings, then each element of `doc_id` is the document ID for each file in the request. Default is None.
            metadata: dict or list of dict
                (Optional) metadata for file(s). If a dict, then the same metadata will be used for all files in the request. If a list of dict, then each element dict is the metadata for each file in the request -- in this case, it is not required that all documents to have the same fields in their metadata. Default is an empty dict.
            verbose: bool
                (Optional) whether to print the detailed information. Default is False.

        Returns
        ---------
            dict | List[dict]
                The response from the Vectara server. If a single file is uploaded, then a dict is returned. If multiple files are uploaded (when ``source`` is a list of filepaths or a folder), then a list of dict is returned.
        """
        if isinstance(source, str):
            if os.path.isfile(source):
                assert doc_id is None or isinstance(doc_id, str), "doc_id must be either empty or a string if source is a single file."
                r = self.upload_file(corpus_id, source, doc_id=doc_id, metadata=metadata, verbose=verbose)
            elif os.path.isdir(source):
                # FIXME: default descrptions for upload_folder() is an empty list. Diff from the default description for upload()).
                assert doc_id is None or isinstance(doc_id, list), "doc_id must be a list if source is a folder."
                r = self.upload_folder(corpus_id, source, doc_ids=doc_id, metadata=metadata, verbose=verbose)
            else:
                print(f"Invalid source {source}")
                exit()
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
    def upload_file(self, corpus_id: int, filepath: str, doc_id: str = "", metadata: Dict = {}, verbose: bool = False) -> Dict:
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

        Parameters
        -----------
            filepaths: str
                paths to files
            doc_ids: str
                alphanumeric IDs for referring to the documents later
            metadata: dict or list of dict
                metadata for files. If a dict, then the same metadata will be used for all files in the request. If a list of dict, then each element is the metadata for each file in the request.
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
              print_format: Literal['json', 'markdown'] = '',
              jupyter_display: bool = False,
              verbose: bool = False
        ) -> Dict:
        """Make a query to a corpus at Vectara

        Examples
        ------------
        >>> import vectara
        >>> client = vectara.vectara() # get default credentials from environment variables
        >>> client.query(
                corpus_id,
                "What if the government fails to protect your rights?",
                metadata_filter="doc.id = 'we the people'",
                top_k=3,
                print_format='json',
                verbose=True
            )

        Parameters
        ------------
            corpus_id: int
                the corpus ID to send the query to
            query: str
                the query (question, search terms) to ask
            top_k: int
                the number of most matching results to return and to summarize
            lang: str
                the ISO 639-1 or ISO 639-3 language code for the language in which a summary is generated. Default: 'auto', letting the Vectara platform to determine.
            contextConfig: dict
                See https://docs.vectara.com/docs/rest-api/query? for details
            return_summary: bool
                whether to return a summary of the top_k results
            metadata_filter: str
                Vectara's metadata filter to narrow down the search results. See https://docs.vectara.com/docs/learn/metadata-search-filtering/filter-overview and for details.

        Returns
        ---------
            dict
                The response from the Vectara server.
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

        if verbose:
            print (json.dumps(payload, indent=2))

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

        if response.status_code != 200:
            print(f"Vectara server returned {response.status_code} error. ")
            print(json.dumps(response.json(), indent=2))
            return {}
        else:
            print("Query successful. ")
            response_dict = response.json()['responseSet'][0]
            summary = response_dict.get('summary', [])
            factualConsistencyScore = -1
            if len(summary) > 0:
                if summary[0].get('text', '') != "":
                    summary = response_dict['summary'][0]['text']
                    factualConsistencyScore = ['factualConsistencyScore']
            self.last_result = {
                "question": query,
                "corpus_id": corpus_id,
                "top_k": top_k,
                "lang": lang,
                "factualConsistencyScore": factualConsistencyScore,
                "raw_response": response.json(),
            }

            beautiful_content = post_process_query_result(
                response.json(), 
                print_format=print_format, 
                jupyter_display=jupyter_display
            )

            if self.from_cli or verbose:    
                print(beautiful_content)

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
    def create_document_from_sections(self,
            corpus_id: int,
            sections: List[str],
            section_ids: List[int] = [],
            section_metadata: List[Dict] = [],
            doc_id: str = "",
            doc_metadata: Dict = {},
            verbose: bool = False) -> Dict:
        """Create a document in a corpus specified by ``corpus_id`` from a list of texts, each of which is a section of the document.

        This is for experts. A document is a collection of sections, each of which is a collection of texts.

        The **difference** between this method and ``create_document_from_chunks`` is that in this methods, you cannot control the chunking of texts but you can hierarchically organize texts (although currently only one level of hierarchy is supported in this SDK).

        Examples
        ------------
        >>> import vectara
        >>> client = vectara.vectara() # get default credentials from environment variables
        >>> client.add_sections(
                corpus_id = 11,
                sections = [
                    "I have one TV. ",
                    "Ich habe einen TV."
                ],
                section_ids = [100, 200],
                section_metadata = [
                    {"language": "English"},
                    {"language": "German"}
                ],
                doc_id = "my apartment",
                doc_metadata = {"genre": "life"},
                verbose = True
            )

        Parameters
        -----------
        corpus_id: int
            the corpus ID to upload to
        sections: list of str
            A section is a concept in document retrieval system. It is the sub-unit of a document. Here multiple sections are being added into a document at once.
        section_ids: list of int
            (Optional) The section IDs for each section. If not provided, the section IDs will be generated by Vectara.
        section_metadata: list of dict
            (Optional) The metadata for each section. If provided, the metadata will be pigged back in the query result. If not provided, the metadata will be empty.
        doc_id: str
            (Optional) The document ID for the document. If not provided, the document will just not have an ID. Note the ID is not a number. It is a string.
        doc_metadata: dict
            (Optional) The metadata for the document. If provided, the metadata will be piggied back in the query result. If not provided, the metadata will be empty.
        verbose: bool
            (Optional) Whether to print the detailed information. Default is False.

        Returns
        --------
        dict
            The response from the Vectara server.

        Notes
        ---------
        1. Vectara does not allow updating a document. If you want to update a document, you need to delete the document first and then re-add content into it.
        2. A section ID must be positive integers. If it is 0, then it will not show up in the metadata of the query return.

        Limitations
        ------------
        Vectara supports hierarchical documents, thus a section can recursively be a collection of sections. However, this method only support one level of hierarchy. We will add the support for more levels in the future.

        References
        ------------
            https://docs.vectara.com/docs/rest-api/index

        """

        url = f"{self.base_url}/v1/index"

        sections_ = [{"text": section} for section in sections]

        if len(section_ids) > 0:
            assert len(section_ids) == len(sections), "Length of section_ids must be the same as the number of sections."
            sections_ = [d | {"section_id": section_id} for d, section_id in zip(sections_, section_ids)]

        if len(section_metadata) > 0:
            assert len(section_metadata) == len(sections), "Length of section_metadata must be the same as the number of sections."
            sections_ = [d | {"metadataJson": json.dumps(metadata)} for d, metadata in zip(sections_, section_metadata)]

        document = {'document_id': doc_id, 'section': sections_}
        if doc_id != "":
            document["document_id"] = doc_id
        if doc_metadata != {}:
            document["metadataJson"] = json.dumps(doc_metadata)

        request = {'customer_id': self.customer_id, 'corpus_id': corpus_id, 'document': document}

        headers = {}

        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        print ("Creating a document from sections...")

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(request)
            )

        if verbose:
            print (response.json())

        return response.json()

    @funix(disable=True)
    def create_document_from_chunks(self,
            corpus_id: int,
            chunks: List[str],
            chunk_metadata: List[Dict] = [],
            doc_id: str = "",
            doc_metadata: Dict = {},
            verbose: bool = False) -> dict:
        """Create a document in a corpus specified by ``corpus_id`` from a list of texts, each of which is a chunk of the document.

        This is for experts. A document is a collection of chunks. Each chunk is a unit in retrieval.

        The difference between this method and ``create_document_from_sections`` is that in this method, you can control the chunking of texts -- a chunk you upload is the retrieval unit -- and all chunks are at the same level, while in ``create_document_from_sections``, you cannot control the chunking of texts and the sections can be hierarchical (although currently only one level of hierarchy is supported in this SDK).

        Parameters
        -----------
            corpus_id: int
                the corpus ID in which to create a document
            chunks: list of str
                the chunks of the document
            chunk_metadata: list of dict
                (Optional) the metadata for each chunk. If provided, the metadata will be pigged back in the query result. If not provided, the metadata will be empty.
            doc_id: str
                (Optional) the document ID for the document. If not provided, the document will just not have an ID. Note the ID is not a number. It is a string.
            doc_metadata: dict
                (Optional) the metadata for the document. If provided, the metadata will be piggied back in the query result. If not provided, the metadata will be empty.
            verbose: bool
                (Optional) whether to print the detailed information. Default is False.

        Returns
        --------
            dict
                the response from the Vectara server.

        """
        url = "https://api.vectara.io/v1/core/index"

        parts = [{"text": chunk} for chunk in chunks]
        if len(chunk_metadata) > 0:
            assert len(chunk_metadata) == len(chunks), "Length of chunk_metadata must be the same as the number of chunks."
            parts = [d | {"metadataJson": json.dumps(metadata)} for d, metadata in zip(parts, chunk_metadata)]
        document = {'document_id': doc_id, 'parts': parts, 'metadataJson': json.dumps(doc_metadata)}
        request = {'customer_id': self.customer_id, 'corpus_id': corpus_id, 'document': document}

        # print (json.dumps(request, indent=2))

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
    def list_jobs(self,
            jobID: int = None,
            corpus_ids: List[int] = None,
            elapsed_seconds: int = None,
            states: List[Literal['QUEUED', 'STARTED', 'COMPLETED', 'FAILED', 'ABORTED', 'UNKNOWN']] = None,
            numResults: int = 10,
            pageKey: str = None
            ) -> dict:
        """List the statuses of jobs.

        All parameters are optional to narrow down the job listing. If no parameters are provided, then the method will return the latested 100 jobs in the past 180 days.

        An example of the response is as follows:

        .. highlight:: json
        .. code-block:: json

            {
                "status": [],
                "job": [
                    {
                    "id": "SDIzYktHMzNHMlJpsbXC8p5IJaONNGgnpbsUViXXkOoqnA==",
                    "type": "JOB__CORPUS_REPLACE_FILTER_ATTRS",
                    "corpusId": [
                        12
                    ],
                    "state": "JOB_STATE__COMPLETED",
                    "tsCreate": "1714181371",
                    "tsStart": "1714181400",
                    "tsComplete": "1714181400",
                    "userHandle": "forrest.bao@gmail.com"
                    },
                    {
                    "id": "SDIzYktHMzNHMlJpsbXC8pRDZL2Iw1JV41cTcneieXc2CA==",
                    "type": "JOB__CORPUS_REPLACE_FILTER_ATTRS",
                    "corpusId": [
                        12
                    ],
                    "state": "JOB_STATE__COMPLETED",
                    "tsCreate": "1714285513",
                    "tsStart": "1714285562",
                    "tsComplete": "1714285562",
                    "userHandle": "forrest.bao@gmail.com"
                    }
                ],
                "pageKey": "e8jhrDQNZwagrBQmcuoGVHUCeaqHF+2TE4nUkm34HPWjm147U6223iT9bO/oa6NKohoQZTT2NuqFRuCqp143g3rIVseAPi0liPTvXfKNc0FGBjuB"
            }

        Parameters
        ------------
            jobID: int
                (Optional) the ID of the job to check
            corpus_ids: List[int]
                (Optional) the corpus ID to list jobs for
            elapsed_seconds: int
                (Optional) only return jobs that were within these many seconds ago. Max allowed value is 180 days ago.
            states: List[Literal['QUEUED', 'STARTED', 'COMPLETED', 'FAILED', 'ABORTED', 'UNKNOWN']]
                (Optional) only return job matching these states
            numResults: int
                (Optional) the number of jobs to return. Max is 100.
            pageKey: str
                (Optional) return the jobs starting from this page

        Returns
        ---------
            dict
                A nested Python dict containing the list of jobs. The structure of the dict is described in this page https://docs.vectara.com/docs/rest-api/list-jobs
        """

        url = f"{self.base_url}/v1/list-jobs"

        headers = {}

        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        payload = {}
        if jobID:
            payload['jobId'] = jobID
        if corpus_ids:
            payload['corpusId'] = corpus_ids
        if elapsed_seconds:
            payload['epochSecs'] = elapsed_seconds
        if states:
            payload['state'] = states
        if numResults:
            payload['numResults'] = numResults
        if pageKey:
            payload['pageKey'] = pageKey

        response = requests.post(url, headers=headers,data=json.dumps(payload))

        return response.json()

    @funix(disable=True)
    def add_corpus_filters(self,
            corpus_id: int,
            name: str,
            type: Literal['text', 'float', 'int', 'bool'],
            level: Literal['document', 'part'],
            description: str = "",
            index: bool=False
            ) -> int:

        """Set the filters for a corpus.

        Parameters
        ------------
            corpus_id: int
                the corpus ID to set filters for
            name: str
                the name of the filter. must match a name in the metadata of the documents in the corpus.
            description: str
                (Optional) the description of the filter
            type: Literal['text', 'float', 'int', 'bool']
                the type of the filter
            level: Literal['document', 'part']
                the level of the filter
            index: bool
                whether to index the filter. Once indexed, searching on it can be faster.

        Returns
        ---------
            int | dict
                A job ID if the request is successful. Else, the response as a nested Python dict for further inspection.
        """

        url = f"{self.base_url}/v1/replace-corpus-filter-attrs"
        headers = {}

        if self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        type_mapping= {'text': 'TEXT', 'float': 'REAL', 'int': 'INTEGER', 'bool': 'BOOLEAN'}

        level_mapping = {'document': 'DOCUMENT', 'part': 'DOCUMENT_PART'}

        payload = {
            "corpusId": corpus_id,
            "filterAttributes": [
                {
                "name": name,
                "description": description,
                "indexed": index,
                "type": f"FILTER_ATTRIBUTE_TYPE__{type_mapping[type]}",
                "level": f"FILTER_ATTRIBUTE_LEVEL__{level_mapping[level]}"
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_json = response.json()
        if response.status_code == 200:
            if 'jobId' in response_json and response_json['jobId']:
                jobId = response_json['jobId']
            else:
                print (response_json)
                return response_json
        else:
            print(response_json)
            return response_json

        print (jobId)

        job_status = self.list_jobs(jobID=jobId)
        start_time = time.time()
        print ("Updating filter attributes...jobID =", jobId)
        while job_status['job'][0]['state'] != 'JOB_STATE__COMPLETED':
            time.sleep(1)
            job_status = self.list_jobs(jobID=jobId)
            if len(job_status["job"]) == 0:
                print("Job done or not found. ")
                break
            else:
                print ("Updating...", job_status['job'][0]['state'], "elapsed time", time.time() - start_time, end="\r")

        print ("Done")
        return jobId

@funix(disable=True)
def post_process_query_result(
    query_result: Dict,
    print_format: Literal['json', 'markdown'] = 'markdown',
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
    except:
        summary = "No summary available."
        factualConsistencyScore = "N/A"

    summary_md = '\n'.join(textwrap.wrap(summary, 100))
    md += f"""\
### Here is the answer
{summary_md if print_format == 'markdown' else summary}

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

    print_format = print_format.lower()

    if print_format == 'markdown':
        if jupyter_display:
            md_obj = Markdown(md)
            display_markdown(md_obj)
        return md
    elif print_format == 'json':
        # md = '```json\n' + json.dumps(simple_result, indent=2) + "\n```"
        md = json.dumps(simple_result, indent=2)
        if jupyter_display:
            display_markdown(Markdown(f"```json\n{md}\n```"))
        return md
