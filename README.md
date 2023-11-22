# An UNofficial Python SDK and CLI for Vectara's RAG platform 

It supports major features of Vectara's RAG platform for you to build your own search engine. 

Additional features: 
* It expands the upload function to allow you to upload a list of files or all files under a directory in one function call. 
* Renders query results in beautiful Markdown printout.

## Installation

```bash
# pip install from Github
pip install "git+https://github.com/forrestbao/vectara-python-cli.git"
```

## Usage 

### Environment variables
This unofficial Vectara SDK gives you the experience consistent with that of OpenAI, Cohere, etc. You can set up your Vectara credentials as environment variables. 

```bash
export VECTARA_CUSTOMER_ID=123
export VECTARA_CLIEND_ID=abc
export VECTARA_CLIENT_SECRET=xyz
```

### Python 
Try the Jupyter notebook `demo.ipynb` or read the docstring. 

```python
from vectara import vectara

client = vectara() # get default credentials from environment variables 
                   # You can also manually pass in your credentials as arguments

corpus_id = client.create_corpus('my knowledge base')

client.upload(corpus_id, 'one_file.pdf', description='My precious doc')  # add one file to the corpus 
client.upload(corpus_id, 'a_folder_of_documents') # add all files under a folder to the corpus
client.upload(corpus_id, ['user_manual.md', 'notes.txt'], description=['user manual', 'my memory']) # add a list of files to the corpus

client.query(corpus_id, 'Vectara allows me to search for anything, right?', top_k=5) # query the corpus for top 5 answers

client.reset_corpus(corpus_id) # delete all documents in the corpus
```

### Command line 
To learn the command line usage, run `vectara --help`. 

You must set up your Vectara credentials as environment variables before using the command line interface. 
    
```bash
# create a corpus
vectara create_corpus 'my knowledge base'
# output: corpus_id = 12

# upload a file to the corpus
vectara upload 12 one_file.pdf # corpurs_id = 12

# upload a folder to the corpus
vectara upload 12 ./a_folder_of_documents # corpurs_id = 12

# query the corpus
vectara query 12 'Vectara allows me to search for anything, right?' --top_k=5  # corpurs_id = 12

# reset the corpus
vectara reset_corpus 12 # corpurs_id = 12
```

### Beautiful Markdown printout 



## Questions
Contact forrest at vectara dot come 

## Disclaimer
This is an UNofficial SDK and CLI for Vectara's RAG platform.
Use at your own risk.
Vectara does NOT provide support for this SDK or CLI.