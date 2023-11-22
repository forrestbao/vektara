from vectara import vectara

client = vectara() # get credentials from environment variables 

corpus_id = client.create_corpus('my knowledge base')

client.upload(corpus_id, 'one_file.pdf', description='My precious doc')  # add one file to the corpus 
client.upload(corpus_id, 'a_folder_of_documents') # add all files under a folder to the corpus
client.upload(corpus_id, ['user_manual.md', 'notes.txt'], description=['user manual', 'my memory']) # add a list of files to the corpus

client.query(corpus_id, 'Vectara allows me to search for anything, right?', top_k=5) # query the corpus for top 5 answers

client.reset_corpus(corpus_id) # delete all documents in the corpus