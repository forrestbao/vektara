#%% 
from vectara import vectara


client = vectara()

corpus_id = 6
client.reset_corpus(corpus_id)


text_list = [
    "Seventy years ago, Anne Frank died of typhus in a Nazi concentration camp at the age of 15.",
    "Just two weeks after her supposed death on March 31, 1945, the Bergen-Belsen concentration camp where she had been imprisoned was liberated -- timing that showed how close the Jewish diarist had been to surviving the Holocaust.",
    "But new research released by the Anne Frank House shows that Anne and her older sister, Margot Frank, died at least a month earlier than previously thought.",
    "Researchers re-examined archives of the Red Cross, the International Training Service and the Bergen-Belsen Memorial, along with testimonies of survivors.",
    "They concluded that Anne and Margot probably did not survive to March 1945 -- contradicting the date of death which had previously been determined by Dutch authorities."
]
id_list = [1, 2, 3, 4, 5]

client.upload_sections(
    corpus_id, 
    text_list, 
    id_list,
    doc_id="source", 
    verbose=True)

client.query(corpus_id, "The Anne Frank House has revealed that Anne Frank and her older sister, Margot, likely died at least a month earlier than previously believed.", print_format= 'json', verbose=True, metadata_filter="doc.id='source'")

# %%
