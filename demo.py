from vectara import vectara, post_process_query_result

client = vectara() # get credentials from environment variables 

corpus_id = client.create_corpus('my knowledge base')

client.upload(corpus_id, 'one_file.pdf', description='A scientific paper')  # add one file to the corpus 
client.upload(corpus_id, 'a_folder_of_documents') # add all files under a folder to the corpus
client.upload(corpus_id, ['README.md', 'demo.py'], description=['README', 'demo code']) # add a list of files to the corpus

r = client.query(corpus_id, 'How to set credentials? ', top_k=5) # query the corpus for top 5 answers, return a JSON string 
print (post_process_query_result(r)) # post process the query result to get a list of answers

r = client.query(corpus_id, 'How to set credentials? ', top_k=5, return_summary=False) # query the corpus for top 5 answers, no summary, just search, return a JSON string
print (post_process_query_result(r)) # post process the query result to get a list of answers

client.reset_corpus(corpus_id) # delete all documents in the corpus