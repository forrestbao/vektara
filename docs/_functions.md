## Summary of Functions

### Administrative 

| Function | Vectara v1 endpoint | Purpose | 
| --- | --- | --- |
| `vectara.acquire_jwt_token()` | N/A because it is through AWS | Acquire OAuth2 token |
| `vectara.list_jobs()` | `list-jobs` | List jobs, with filters if applicable |

### Corpus management

| Function | Vectara v1 endpoint | Purpose | 
| --- | --- | --- |
| `vectara.create_corpus()` | `create-corpus` | Create a new corpus |
| `vectara.reset_corpus()` | `reset-corpus` | Remove all documents in a corpus but keeping the metadata if there is any |
| `vectara.list_documents()` | `list-documents` | List documents in a corpus |
| `vectara.delete_document()` | `delete-doc` | Delete a document in a corpus |
| `vectara.set_corpus_filters()` | `replace-corpus-filter-attrs` | Set certain metadata fields to filterable | 

### Adding content to a corpus 

| Function | Vectara v1 endpoint | Purpose | 
| --- | --- | --- |
| `vectara.upload()` | `fileUpload` | Upload a single file, a list of files, or an entire folder. Supports adding metadata. |
| `vectara.create_document_from_sections()` | `index` | Create a document by adding texts with hierarchy, like a book consisting of chapters consisting of sections, etc. But you have no control over how texts are chunked. |
| `vectara.create_document_from_chunks()` | `core/index` | Create a document by adding text chunks without hierarchy. Each chunk becomes a unit in retrieval. |

### Querying a corpus

| Function | Vectara v1 endpoint | Purpose |
| --- | --- | --- |
| `vectara.query()` | `query` | Query a corpus. Supports filtering. |