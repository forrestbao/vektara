from vectara import Vectara, post_process_query_result

V = Vectara() # get credentials from environment variables 

corpus_id = V.create_corpus('America, the Beautiful') # create a new corpus

V.upload(corpus_id, 'test_data/consitution_united_states.txt') # upload one file 

V.upload(corpus_id, ['test_data/consitution_united_states.txt', 'test_data/declaration_of_independence.txt'])  # upload a list of files 

V.upload(corpus_id, "test_data") # upload all files in a folder, no recursion 

V.query(corpus_id, "What if the government infringes your rights?", print_format= 'markdown', verbose=True) # query the corpus

V.reset_corpus(corpus_id) # delete all documents in the corpus, if needed. 