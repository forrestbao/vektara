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

from funix import funix_class, funix_method
from funix.hint import BytesFile

vectara_config = ".vectara_config"

def md2text(md: str):
    html = markdown.markdown(md)
    soup = bs4.BeautifulSoup(html, features='html.parser')
    return soup.get_text()

@funix_class()
class vectara():
    @funix_method(
        title="Initialize Vectara",
        print_to_web=True,
        widgets= { # this is needed because the SDK also needs to remain compatible with Google Fire.
                   # If using Funix only, we can set the type to ipywidgets.password instead of str
            'client_id': 'password',
            'client_secret': 'password'
        }
    )
    def __init__(self, base_url = "https://api.vectara.io", customer_id: str = "", client_id: str = "", client_secret: str = "", from_cli: bool = False):
        def get_env(env: str, default: str) -> str:
            result = os.environ.get(env, default)
            if result is None or result.isspace() or len(result) == 0:
                raise TypeError(f"Expected a env `{env}`, but it's not set or empty.")
            return result

        customer_id = get_env('VECTARA_CUSTOMER_ID', customer_id)
        client_id = get_env('VECTARA_CLIENT_ID', client_id)
        client_secret = get_env('VECTARA_CLIENT_SECRET', client_secret)
        base_url = get_env('VECTARA_BASE_URL', base_url)

        def is_true(value: str) -> bool:
            return value.lower() in ['true', 'yes', '1']

        self.proxy_mode = is_true(os.environ.get('VECTARA_PROXY_MODE', 'false'))

        if base_url != "https://api.vectara.io":
            self.proxy_mode = True # force proxy mode if base_url is not the default

        self.customer_id = customer_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.from_cli = from_cli

        if not from_cli:
            self.jwt_token = self.acquire_jwt_token()
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

        jwt_token = response.json()["access_token"]

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

        jwt_token = self.jwt_token if not self.from_cli else self.acquire_jwt_token()
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
            "customer-id": f"{self.customer_id}",
            # Customer ID must be there. Otherwise, error-16, "Request does not contain customer-id-bin header."
            "Authorization": f"Bearer {jwt_token}"
        }

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

        jwt_token = self.jwt_token if not self.from_cli else self.acquire_jwt_token()
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/reset-corpus"

        payload = json.dumps(
            {
                "corpusId": corpus_id
            }
        )

        headers = {
            "customer-id": f"{self.customer_id}",
            # Customer ID must be there. Otherwise, error-16, "Request does not contain customer-id-bin header."
            "Authorization": f"Bearer {jwt_token}"
        }

        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            print(f"Resetting corpus {corpus_id} successful. ")
        else:
            print(f"Failed resetting corpus {corpus_id}. ")
            print(response.json())

        return None

    @funix_method(disable=True)
    def upload(self, corpus_id: int, source: str | List[str], description: str | List[str] = "", verbose: bool = False):
        """Upload a file, a list of files, or files in a folder, to a corpus specified by corpus_id

        params:
            corpus_id: the corpus ID to upload to
            source: the source to upload, a file, a list of files, or a folder
            description: the description to the file
        """
        if isinstance(source, str):
            if os.path.isfile(source):
                self.upload_file(corpus_id, source, description, verbose=True)
            elif os.path.isdir(source):
                # FIXME: default descrptions for upload_folder() is an empty list. Diff from the default description for upload()).
                self.upload_folder(corpus_id, source, description, verbose)
            else:
                print("Invalid source. ")
        elif isinstance(source, list):
            # FIXME: default descrptions for upload_files() is an empty list. Diff from the default description for upload()).
            self.upload_files(corpus_id, source, description, verbose)
        else:
            print("Invalid source. ")

    @funix_method(print_to_web=True, title="Upload file")
    def upload_file_from_funix(self, corpus_id: int, filebuf: BytesFile, description: str = "", verbose: bool = False) -> Markdown:
        """Drag and drop a file to Funix frontend to add it to a corpus specified by corpus_id
        """
        jwt_token = self.jwt_token if not self.from_cli else self.acquire_jwt_token()

        url = f"{self.base_url}/v1/upload?c={self.customer_id}&o={corpus_id}"

        if description == "":
            description = "A file uploaded via Funix"

        file_payload = (
            'file',
            (description,
             io.BytesIO(filebuf),
             'application/octet-stream')
        )

        headers = {
            'Authorization': f'Bearer {jwt_token}'
        }

        print(f"Uploading file **{description}** to corpus **{corpus_id}**...")

        response = requests.post(
            url,
            headers=headers,
            # data=payload,
            files=[file_payload]
        )

        if response.status_code == 200:
            print("### **Success.** ")
        else:
            print("### **Failed.** ")
            print(response.json())

        return None

    @funix_method(disable=True)
    def upload_file(self, corpus_id: int, filepath: str, description: str = "", verbose: bool = False):
        """Upload a file from local storage to a corpus specified by corpus_id

        params:
            corpus_id: the corpus ID to upload to
            filepath: path to file
            description: the description to the file
        """
        jwt_token = self.jwt_token if not self.from_cli else self.acquire_jwt_token()
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/upload?c={self.customer_id}&o={corpus_id}"

        if description == "":
            description = os.path.basename(filepath)

        file_payload = (
            'file',
            (description,
             open(filepath, 'rb'),
             'application/octet-stream')
        )

        headers = {
            'Authorization': f'Bearer {jwt_token}'
        }

        if verbose:
            print(f"Uploading...{filepath}", end=" ")

        response = requests.post(
            url,
            headers=headers,
            # data=payload,
            files=[file_payload]
        )

        if verbose or self.from_cli:
            if response.status_code == 200:
                print("Success. ")
            else:
                print("Failed. ")
                print(response.json())

        return None

    @funix_method(disable=True)
    def upload_files(self, corpus_id, filepaths: List[str], descriptions: List[str] = [], verbose: bool = False):
        """Upload a list of files from local storage

        params:
            filepaths: paths to files
            descriptions: the descriptions to the files
        """

        if len(descriptions) < len(filepaths):
            descriptions = list(map(os.path.basename, filepaths))

        for description, filepath in (
            pbar := tqdm(zip(descriptions, filepaths), total=len(filepaths), desc="Uploading...")):
            pbar.set_postfix_str(filepath)
            self.upload_file(corpus_id, filepath, description, verbose)

    @funix_method(disable=True)
    def upload_folder(self, corpus_id: str, dirpath: str, descriptions: List[str] = [], verbose: bool = False):
        """Upload all files from a directory
        """

        print("Uploading files from folder:", dirpath)
        files = [os.path.join(dirpath, file) for file in os.listdir(dirpath)]

        self.upload_files(corpus_id, files, descriptions, verbose)

    @funix_method(disable=True)
    def query(self,
              corpus_id: int,
              query: str,
              top_k: int = 5,
              lang: str = 'auto') -> Dict:
        """Make a query to a corpus at Vectara

        params:
            corpus_id: the corpus ID to send the query to
            query: the query (question, search terms) to ask
            top_k: the number of most matching results to return and to summarize
            lang: the language in which a summary is generated
            return_format: the return format, 'json' for raw Vectara server return and ''
            is_jupyter: whether to print results in Jupyter
        """
        jwt_token = self.jwt_token if not self.from_cli else self.acquire_jwt_token()
        # TODO: Check whether token is expired.
        # TODO: Load JWT_Token from dotenv if in CLI mode.

        url = f"{self.base_url}/v1/query"

        payload = json.dumps(
            {
                "query": [
                    {
                        "query": query,
                        "numResults": top_k,
                        "corpusKey": [
                            {
                                # "customerId": customer_id,
                                "corpusId": corpus_id,
                            }
                        ],
                        'summary': [
                            {
                                'maxSummarizedResults': top_k,
                                'responseLang': lang
                            }
                        ]
                    }
                ]
            }
        )

        headers = {
            # 'Content-Type': 'application/json',
            # 'Accept': 'application/json',
            'customer-id': self.customer_id,
            'Authorization': f'Bearer {self.jwt_token}'
        }

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code != 200:
            print(f"Vectara server returned {response.status_code} error. ")
            print(response.json())
            return {}
        else:
            print("Query successful. ")
            if self.from_cli:
                simple_json = post_process_query_result(response.json(), format='json')
                print(json.dumps(simple_json, indent=2))
            else:
                return response.json()

    @funix_method(title="Query")
    def query_funix(self, corpus_id: int,
                    query: str,
                    top_k: int = 5,
                    lang: str = 'auto') -> Markdown:
        return post_process_query_result(self.query(corpus_id, query, top_k, lang))


def post_process_query_result(
    query_result: Dict,
    format: Literal['json', 'markdown'] = 'markdown',
    jupyter_display: bool = False) -> Markdown | str:
    """Postprocess query results in Vectara's JSON into a simpler dictionary and a Markdown string for displaying

    jupyter_display: whether to display the result in a Jupyter notebook. Useful if using in Jupyter notebooks.
    """

    # TODO: Extract title from metadata for each document.

    md = ""

    answers = query_result['responseSet'][0] # Since we only make one query each time, there is only one element in the responseSet

    summary = answers['summary'][0]['text']

    summary_md = '\n'.join(textwrap.wrap(summary, 60))
    md += f"""\
### Here is the answer
{summary}

### References:
    """

    simple_result = {'summary': summary, 'matches': []}

    for number, answer in enumerate(answers['response']):
        src_doc_id = answer['documentIndex']
        src_doc_name = answers['document'][src_doc_id]['id']

        simple_result['matches'].append(
            {
                'src_doc_id': src_doc_id,
                'src_doc_name': src_doc_name,
                'text': answer['text']
            }
        )

        md += \
f"""
{number+1}. From document **{src_doc_name}** (matchness={answer['score']}):
  _...{md2text(answer['text'])}..._
"""

    format = format.lower()

    if format == 'markdown':
        if jupyter_display:
            md_obj = Markdown(md)
            display_markdown(md_obj)
        return md
    elif format == 'json':
        md = '```json\n' + json.dumps(simple_result, indent=2) + "\n```"
        if jupyter_display:
            display_markdown(Markdown(md))
        return json.dumps(md, indent=2)
