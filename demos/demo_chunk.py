#%% 
# This demo shows an advanced usage of Vectara where you control chunking. 

from vectara import Vectara, Filter

# Initialize the client
client = Vectara()

# Create a corpus (not always needed)
# corpus_id = client.create_corpus('America, the Beautiful') # create a new corpus

corpus_id = 2
client.reset_corpus(corpus_id) # delete all documents in the corpus, CAUTION and not always needed

text_list = [
    'we the people of the united states in order to form a more perfect union do ordain and establish this constitution for the united states of america.', 
    'Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble'
    ]

client.create_document_from_chunks(
    corpus_id, 
    chunks=text_list, 
    chunk_metadata=[
        {'note': 'preamble'}, 
        {'note': '1st amendment'}], 
    doc_id="Constitution", 
    doc_metadata={"country": "United States"}, 
    verbose=True)

# Set two filters, one at the document level and one at the chunk level
filters: Filter = [
    Filter(name="country", type='str', level='doc', index=True),
    Filter(name="note", type='str', level='part', index=False)
]

client.set_corpus_filters(corpus_id, filters) # set filters to the corpus

r= client.query(
    corpus_id, "What is the Constitution for?", 
    print_format= 'json', 
    return_summary=True,
    # metadata_filter="doc.coutry='United States'", 
    metadata_filter="part.note='preamble'",
    verbose=True) # query the corpus

