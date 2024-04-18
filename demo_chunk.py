#%% 
from vectara import vectara

# Initialize the client
client = vectara()

corpus_id = 12 
client.reset_corpus(corpus_id) # delete all documents in the corpus


text_list = ['we the people', 'of the united states', 'in order to form a more perfect union', 'do ordain and establish this constitution for the united states of america']

client.upload_chunk(
    corpus_id, 
    text_list, 
    doc_id="Constitution", 
    metadata={"type": "summ"}, 
    verbose=True)

client.query(corpus_id, "What if the government infringes your rights?", print_format= 'json', verbose=True, metadata_filter="doc.id='Constitution'") # query the corpus
# client.reset_corpus(corpus_id) # delete all documents in the corpus