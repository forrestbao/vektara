from vektara import Vectara, post_process_query_result

client = Vectara() # get credentials from environment variables 

corpus_id = client.create_corpus('America, the Beautiful') # create a new corpus
### OR 
# corpus_id = 7 # use an existing corpus

client.upload(corpus_id, 'test_data/consitution_united_states.txt') # upload one file 

client.upload(corpus_id, ['test_data/consitution_united_states.txt', 'test_data/declaration_of_independence.txt'])  # upload a list of files 

client.upload(corpus_id, "test_data") # upload all files in a folder, no recursion 

client.query(corpus_id, "What if the government infringes your rights?", print_format= 'markdown', verbose=True) # query the corpus

client.reset_corpus(corpus_id) # delete all documents in the corpus, if needed. 