#%% 
from vectara import vectara


client = vectara()

corpus_id = 6
client.reset_corpus(corpus_id)


text_list = [
    "I am having beer",
    "I am watching TV"
]
id_list = [1, 2]

client.upload_sections(
    corpus_id, 
    text_list, 
    id_list,
    doc_id="source", 
    verbose=True)

client.query(corpus_id, "What do I own?", print_format= 'json', verbose=True, metadata_filter="doc.id='source'")

# %%
