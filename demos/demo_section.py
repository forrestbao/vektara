#%% 
from vectara import vectara

client = vectara()

corpus_id =12
client.reset_corpus(corpus_id)

sections = [
    "I am having beer",
    "I am watching TV"
]

section_ids = [100, 200]

section_metadata = [{"raw_text": text} for text in sections]

doc_metadata = {"raw_doc": " ".join(sections)}

r = client.add_sections(
    corpus_id, 
    sections=sections, 
    section_ids = section_ids,
    section_metadata=section_metadata, 
    doc_id="life",
    doc_metadata=doc_metadata, 
    verbose=True)

client.query(corpus_id, "What am I doing?", print_format= 'json', verbose=True)