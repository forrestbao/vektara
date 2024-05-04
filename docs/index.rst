.. Unofficial Vectara Python SDK/CLI/GUI documentation master file, created by
   sphinx-quickstart on Fri Apr 26 14:57:57 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Reference of ``vectara-python-cli``, an unofficial Vectara Python SDK/CLI/GUI!
========================================================================================

``vectara-python-cli`` is a Python SDK/CLI/GUI that allows you to use Vectara's semantic search and knowledge-based GenAI service in three interfaces: 

1. A Python class (``import vectara``) and its member methods
2. The command line (powered by Google Fire)
3. A GUI (powered by `Funix.io <http://funix.io>`_)

To install, simply run:
``pip install vectara``

The usage and examples can be found in the `README page <https://github.com/forrestbao/vectara-python-cli/blob/main/README.md>`_ of the project. This documentation here is just the API reference. 

`vectara-python-cli` is unofficially maintained by employees and users of Vectara. 


Functions
---------

Administrative
^^^^^^^^^^^^^^^

+-----------------------------------+--------------------------+----------------------------------+
| Function                          | Vectara endpoint         | Purpose                          |
+===================================+==========================+==================================+
| ``vectara.acquire_jwt_token()``   | N/A because it is        | Acquire OAuth2 token             |
|                                   | through AWS              |                                  |
+-----------------------------------+--------------------------+----------------------------------+
| ``vectara.list_jobs()``           | ``list-jobs``            | List jobs, with filters if       |
|                                   |                          | applicable                       |
+-----------------------------------+--------------------------+----------------------------------+

Corpus management
^^^^^^^^^^^^^^^^^^

+--------------------------------------+---------------------------+---------------------------------------------------+
| Function                             | Vectara endpoint          | Purpose                                           |
+======================================+===========================+===================================================+
| ``vectara.create_corpus()``          | ``create-corpus``         | Create a new corpus                               |
+--------------------------------------+---------------------------+---------------------------------------------------+
| ``vectara.reset_corpus()``           | ``reset-corpus``          | Remove all documents in a corpus but keeping      |
|                                      |                           | the metadata if there is any                      |
+--------------------------------------+---------------------------+---------------------------------------------------+
| ``vectara.list_documents()``         | ``list-documents``        | List documents in a corpus                        |
+--------------------------------------+---------------------------+---------------------------------------------------+
| ``vectara.add_corpus_filter()``      | ``replace-corpus-filter-  | Set certain metadata fields to filterable         |
|                                      | attrs``                   |                                                   |
+--------------------------------------+---------------------------+---------------------------------------------------+

Adding content to a corpus 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------------------------------------+-------------------+-----------------------------------------------------------------------------------+
| Function                                      | Vectara endpoint  | Purpose                                                                           |
+===============================================+===================+===================================================================================+
| ``vectara.upload()``                          | ``fileUpload``    | Upload a single file, a list of files, or an entire folder. Supports adding       |
|                                               |                   | metadata.                                                                         |
+-----------------------------------------------+-------------------+-----------------------------------------------------------------------------------+
| ``vectara.create_document_from_sections()``   | ``index``         | Create a document by adding texts with hierarchy, like a book consisting          |
|                                               |                   | of chapters consisting of sections, etc. But you have no control over             |
|                                               |                   | how texts are chunked.                                                            |
+-----------------------------------------------+-------------------+-----------------------------------------------------------------------------------+
| ``vectara.create_document_from_chunks()``     | ``core/index``    | Create a document by adding text chunks without hierarchy. Each chunk             |
|                                               |                   | becomes a unit in retrieval.                                                      |
+-----------------------------------------------+-------------------+-----------------------------------------------------------------------------------+

Querying a corpus 
^^^^^^^^^^^^^^^^^^   

+------------------------+------------+------------------------------------+
| Function               | Vectara    | Purpose                            |
|                        | endpoint   |                                    |
+========================+============+====================================+
| ``vectara.query()``    | ``query``  | Query a corpus. Supports filtering.|
+------------------------+------------+------------------------------------+


The ``vectara`` class 
-----------------------

Please use the navigation on the left to find the method.

.. automodule:: vectara
.. autoclass:: vectara
   :members: acquire_jwt_token, create_corpus, reset_corpus, list_documents, list_jobs, upload, query, create_document_from_sections, create_document_from_chunks
   :special-members: __init__


Indices and tables
==================
* :ref:`search`
