#%% 
from vectara import vectara, post_process_query_result
import json

client = vectara(
    api_key="ABC", 
    customer_id="123"
) # manually set the API key and customer ID instead of getting them from environment variables.

corpus_id = client.create_corpus('America, the Beautiful') # create a new corpus

client.upload(
    corpus_id, 
    'test_data/consitution_united_states.txt', 
    doc_id='we the people', 
    metadata={
        'number of amendements': '27', 
        'Author': 'Representatives from 13 states', 
        'number of words': 4543
        }, 
    verbose=True)

client.query(
    corpus_id, 
    "What if the government fails to protect your rights?", 
    metadata_filter="doc.id = 'we the people'", 
    top_k=3, print_format='json')


client.upload(
    corpus_id, 
    ['test_data/consitution_united_states.txt', 'test_data/declaration_of_independence.txt', 'test_data/gettysburg_address.txt'], 
    doc_id=[
        'the rights', 
        'the beginning', 
        'the war'
    ], 
    metadata=[
        {'Last update': 'May 5, 1992', 'Author': "U.S. Congress"}, # the 27th amendment was ratified on May 5, 1992. 
        {'Location': 'Philadelphia, PA', 'Author': "Thomas Jefferson et al."}, # Declaration of Independence
        {'Location': 'Gettysburg, PA', 'Author': 'Abraham Lincoln', 'Date': 'November 19, 1863'} # Gettysburg Address
    ]
    )

client.query(
    corpus_id, 
    "What if the government infringes your rights?", 
    top_k=3, 
    metadata_filter="doc.id = 'the war' or doc.id='the beginning'", print_format='json')

client.reset_corpus(corpus_id) # delete all documents in the corpus