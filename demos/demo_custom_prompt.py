# This is an advanced demo of Vectara 
# Why it is advanced?
# 1. It uses a customized, non-summarization prompt template to generate text from query results. 
# 2. It adds document-level and chunk-level metadata and filters content for search. 
# 3. It has pagination. 

#%% 


from vektara import Vectara, Filter
import json

V = Vectara()

# corpus_id = V.create_corpus('America, the Beautiful') # create a new corpus

corpus_id = 8 # use an existing corpus
V.reset_corpus(corpus_id) # delete all documents in the corpus

V.upload(
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

prompt_template_string = ('['
'  {"role": "system", "content": "You are a history teacher."}, '
'  #foreach ($qResult in $vectaraQueryResults) '
'     {"role": "user", "content": "Give me the $vectaraIdxWord[$foreach.index] search result."}, '
'     {"role": "assistant", "content": "${qResult.getText()}" }, ' 
'  #end '
'  {"role": "user", "content": "Explain the historical background of the above results to a 5-year-old."} '
']'
)

V.query(
    corpus_id, 
    "What if the government infringes your rights?", 
    top_k=3,
    offset=5, 
    do_generation=True,
    prompt_template_string=prompt_template_string,
    metadata_filter="doc.id = 'the war' or doc.id='the beginning'", print_format='json', 
    verbose=True)

V.reset_corpus(corpus_id) # delete all documents in the corpus