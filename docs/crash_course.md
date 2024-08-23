# A crash course of RAG and `vektara`

This document explains the concept of RAG (Retrieval-Augmented Generation) using a coding demo in `vektara`, a Python SDK for Vectara's RAG platform.

## TL;DR: Just five lines of code 
```python
from vektara import Vectara #  pip install vektara
client = Vectara()
corpus_id = client.create_corpus('The laws of the free world')
client.upload(corpus_id, './test_data/US_Constition.txt')
A = client.query(corpus_id, 'Can people own guns?')
```

## What can RAG do for me? 

Suppose you have some questions about a great amount of texts (e.g., laws in your country), but obviously you cannot read through and remember all of them. RAG (Retrieval-Augmented Generation) is the technology to do two things for you: 
1. The R part: finding sentences in the laws that are relevant to your questions
2. The G part: generating the answer to your questions from the sentences found in the R part


```{mermaid}
    graph LR
    C[The laws] --> B{R}
    A[Your question] --> B
    subgraph RAG
        B --> D[The <br> relevant <br> sentences]
        D --> E{G}
    end
    A --> E{G}
    E --> F[The answer]    
```

## Using `vektara` to do RAG

The core of the module `vektara` that you can pip install (`pip install vektara`) is a class called `Vektara`. 

### Authentication and Initialization

Vectara is a cloud platform. To talk to it, and to ensure that only you can access your data, you need to get credentials -- think them as the username and password. So, **register an account first!** The username in Vectara is called a customer ID, which you can find out [here](https://docs.vectara.com/docs/console-ui/vectara-console-overview#view-the-customer-id). The password is roughly equivalent to a personal API key at Vectara. To get the API key, go to the [Vectara console](https://docs.vectara.com/docs/console-ui/personal-api-key).

Then you can initialize an instance `client` of the `Vectara` class: 

```python
from vektara import Vectara
client = Vectara(customer_id=123, api_key='abc')
```

It might be dangerous to hardcode your credentials in your code. A better way is to save them in a file, say `credentials.sh`: 
```bash
export VECTARA_CUSTOMER_ID=123
export VECTARA_API_KEY=abc
```
and then `source` it before running your code: 
```bash
source credentials.sh
```

In this second way, you can initialize the client without passing in the credentials: 
```python
from vektara import Vectara
client = Vectara()
```

### Corpora

In RAG, the collection of texts to which you ask questions is called a **corpus** (plural "corpora"). You can create a corpus by calling the `create_corpus` method: 
```python
corpus_id = client.create_corpus('The laws of the free world')
```

This will return you a unique, internal ID for the corpus, e.g., `2`. Hold this number carefully because you will need it later.

### Ingestion/Uploading

Before Vectara (the platform) can answer questions for you, you need to add the texts which potentially contain the answers to a corpus. This process is known as **ingestion** which has several steps: 
1. **Chunking**: Texts are segmented into short units known as **chunks**. This allows the R part of RAG to fetch short sentences (e.g., individual articles, sentences, or clauses of the law) that can be specific to your question.
2. **Indexing**: Each chunk is converted into a format that can be quickly searched. Today, this is usually done with a technique called **embedding** where each chunk is represented as a vector.
3. Adding the **metadata**: Metadata are information can be useful to filter the chunks. For example, you can add the type of the law (e.g., patent law, criminal law) as metadata and then later you can limit the search to only the patent laws.

Because the data can be very large, you have to do it batch by batch. Each batch is called a **document**. A document cannot be modified once it is ingested. If you need to update a document, you need to delete it and re-ingest it. Once ingested, each document has a unique `doc_id` in its corpus. 

The `vektara` SDK supports three ways to ingest data to a corpus which will be discussed below. 

#### Autopilot Ingestion

In autopilot ingestion, you provide a (list of) local file or folder, and `vektara` will take care of the rest. Supported file types include PDF, DOCX, and TXT. 
```python
V.upload(
    corpus_id, # the corpus ID obtained above
    './test_data/US_Constition.txt' # a local file. can be a folder or list of files
    )
```
By default, the `doc_id` is the file name. For customizing the `doc_id`'s and metadata, please refer to [`demos/demo_simple.py`](https://github.com/forrestbao/vectara-python-cli/blob/main/demos/demo_simple.py). 

#### i-chunk Ingestion

In i-chunk ingestion, you chunk the texts yourself and upload the chunks. All chunks are at the same level without any hierarchy. The function to use is the function `create_document_from_chunks()` of the `Vectara` class.

```python
chunks = [
    'we the people of the united states in order to form a more perfect union do ordain and establish this constitution for the united states of america.', 
    'Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble'
    ]

client.create_document_from_chunks(
    corpus_id, # the corpus ID obtained above
    chunks=chunks, # mandatory argument
    # optional arguments below
    chunk_metadata=[ 
        {'note': 'preamble'},  
        {'note': '1st amendment'}], 
    doc_id="Constitution", 
    doc_metadata={"country": "United States"}
    # End of optional arguments
    )
```

For now let's ignore the purpose of the optional arguments `chunk_metadata` and `doc_metadata`. We will discuss them later [here](#making-use-of-the-metadata). 

The full demo is in [`demos/demo_simple.py`](https://github.com/forrestbao/vektara/blob/main/demos/demo_simple.py)

#### Hierarchical Ingestion
This is the most advanced way to ingest data. You upload texts as a hierarchical structure, like a book consisting of chapters consisting of sections ... paragraphs ... sentences. The nesting is unlimited. Chunking is done automatically by Vectara. However, if you break texts down to very short segments, you implicitly control the chunking. We will skip examples here. If you are interested, please refer to [`demos/demo_section.py`](https://github.com/forrestbao/vektara/blob/main/demos/demo_section.py)

### Querying 

Now we have come to the most exciting part: asking questions to the corpus. The `query` method is used for this purpose. 

```python
A = client.query(
    corpus_id,   # the corpus ID obtained above, mandatory
    "What is the Constitution for?"  # the query, mandatory
    )
```

The return `A` is nested dictionary like this: 

```json
{
  "summary": {
    "text": "The Constitution is the foundational legal document for the United States, established by the people to create a more perfect union [1]. It outlines the structure of the government and protects fundamental rights such as freedom of religion, speech, press, and assembly [2]. The Constitution serves as a framework for governance, setting forth the principles and rules by which the country is governed and providing a system of checks and balances to prevent any one branch from becoming too powerful.",
    "factualConsistencyScore": 0.11672028
  },
  "references": [
    {
      "doc_index": 0,
      "doc_id": "Constitution",
      "text": "we the people of the united states in order to form a more perfect union do ordain and establish this constitution for the united states of america.",
      "matchness": 0.7463158
    },
    {
      "doc_index": 0,
      "doc_id": "Constitution",
      "text": "Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble",
      "matchness": 0.69059783
    }
  ]
}
```

Three things are returned:
1. `summary`: a summary of the answer.
2. `references`: the chunks that are relevant to the question. Each chunk has a `matchness` score indicating how relevant it is to the question. Because we have only two chunks here, only two chunks are returned.
3. `factualConsistencyScore`: a score indicating how consistent the answer is with the facts in the corpus. Unfortunately, the LLM used to generate the summary inserted too much of its own knowledge which are not supported by the references, so this score was low.

### Multilingual Support

In the demo so far, we only asked questions to the US Constitution. What about other countries? 

To do so, let's create a new document with the first sentence in the preamble of the constitution of Korea. 

```python
client.create_document_from_chunks(
    corpus_id, # the corpus ID obtained above
    chunks = [
        '悠久한 歷史와 傳統에 빛나는 우리 大韓國民은 3·1運動으로 建立된 大韓民國臨時政府의 法統과 不義에 抗拒한 4·19民主理念을 繼承하고, 祖國의 民主改革과 平和的統一의 使命에 立脚하여 正義·人道와 同胞愛로써 民族의 團結을 鞏固히 하고, 모든 社會的弊習과 不義를 打破하며, 自律과 調和를 바탕으로 自由民主的基本秩序를 더욱 確固히'
        ],
    # optional arguments below
    chunk_metadata = [{'note': 'preamble'}], 
    doc_id = "Constitution of Korea", 
    doc_metadata = {"country": "Korea"}
    # End of optional arguments
    )
```

Then let's ask a question to the corpus: 
```python
A = client.query(
    corpus_id,   # the corpus ID obtained above, mandatory
    "What is the constitution of Korea for?"  # the query, mandatory
    )
```

The answer `A` is

```json
{
  "summary": {
    "text": "The Constitution of Korea serves to uphold the principles of justice, humanity, and patriotism, aiming to strengthen national unity and break societal injustices. It inherits the legacy of the Korean Provisional Government and the democratic ideals of the April 19 Movement, focusing on democratic reforms and peaceful reunification efforts. Based on a foundation of self-discipline and harmony, the Constitution aims to solidify a free and democratic order, rooted in the country's rich history and traditions [1].",
    "factualConsistencyScore": "None"
  },
  "references": [
    {
      "doc_index": 0,
      "doc_id": "Constitution of Korea",
      "text": "悠久한 歷史와 傳統에 빛나는 우리 大韓國民은 3·1運動으로 建立된 大韓民國臨時政府의 法統과 不義에 抗拒한 4·19民主理念을 繼承하고, 祖國의 民主改革과 平和的統一의 使命에 立脚하여 正義·人道와 同胞愛로써 民族의 團結을 鞏固히 하고, 모든 社會的弊習과 不義를 打破하며, 自律과 調和를 바탕으로 自由民主的基本秩序를 더욱 確固히",
      "matchness": 0.770589
    },
    {
      "doc_index": 1,
      "doc_id": "Constitution",
      "text": "we the people of the united states in order to form a more perfect union do ordain and establish this constitution for the united states of america.",
      "matchness": 0.6708078
    },
    {
      "doc_index": 1,
      "doc_id": "Constitution",
      "text": "Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble",
      "matchness": 0.6490252
    }
  ]
}
```

Wow, what just happened? The answer is based on the content of the Korean Constitution, while the references are from both the Korean and US Constitutions. The matchness score of the Korean Constitution is higher than that of the US Constitution. Vectara is a language-agnostic platform that supports cross-lingual RAG. More challenging, the original text of the Korean Constitution was written in 1940s in a mixture of Hangul (the Korean alphabet) and Hanja (Chinese characters) -- kinda like Japanese Kana and Kanji, yet Vectara can handle them along with English well. The `factualConsistencyScore` is `NaN` because currently Vectara's hallucination detection model does not support Korean. 

### Filtering with metadata

What if I only wanna ask questions to the US Constitution? You can use the metadata to filter the data. 

Vectara supports two levels of metadata: doc and chunk. Doc metadata is associated with the whole document, while chunk metadata is associated with each chunk. You can only set the chunk-level metadata in the i-chunk and hierarchical ingestion modes.

A metadata can be access using the simple dot syntax `{level}.{name}` where `level` is either `doc` (doc-level) or `part` (chunk-level). For example, to access the metadata `country` of the document, you can use `doc.country`. By default, each document has a metadata field `doc_id` which is the `doc_id` you set or automatically set when ingesting the document. You need to make sure that the `name` is already set. 

To filter, you must first enable the metadata fields on which you wanna filter to be filterable. This is done by calling the `set_corpus_filters` method. 

```python
from vektara import Filter
from typing import List

filters: List[Filter] = [
    Filter(name="country", type='str', level='doc', index=True),
    Filter(name="note", type='str', level='part', index=False)
]

client.set_corpus_filters(corpus_id, filters)
```

The 2nd argument of `set_corpus_filters` method is a list of `Filter` objects. A `Filter` object has the following attributes:
```
    name: str
    type: Literal['str', 'float', 'int', 'bool']
    level: Literal['doc', 'part']
    description: str = ''
    index: bool = False
```
where the `index` attributes to index the attributes so we can search and filter faster. 

Finally, by asking questions like below (the `metadata_filter` of `query`), the answer will come from the US Constitution only.

```python
A = client.query(
    corpus_id, 
    "What is the Constitution for?", 
    metadata_filter="doc.coutry='United States'"  # only asks to the document whose `country` is 'United States'
    )
```

## Conclusion

This document has shown you how to use the `vektara` SDK to do RAG. If you like the `vektara` SDK, please give it a star on [GitHub](https://github.com/forrestbao/vektara/) and spread the word. If you have any questions, please open an issue on GitHub.

Options expressed in this document are only those of the authors and do not necessarily represent the views of Vectara. 
