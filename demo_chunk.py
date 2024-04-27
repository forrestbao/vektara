#%% 
# This demo shows an advanced usage of Vectara where you control chunking. 

from vectara import vectara

# Initialize the client
client = vectara()

corpus_id = 12 
# client.reset_corpus(corpus_id) # delete all documents in the corpus

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

client.query(corpus_id, "What is the Consitution for?", print_format= 'json', metadata_filter="doc.country='United States'") # query the corpus