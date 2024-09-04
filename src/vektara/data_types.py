from typing import List, Literal, Dict

import pydantic 

class Filter(pydantic.BaseModel):
    """A filter to be set on a corpus.

    for `level`, `part` means chunk-level. 
    """
    name: str
    type: Literal['str', 'float', 'int', 'bool']
    level: Literal['doc', 'part']
    description: str = ''
    indexed: bool = False

class Message(pydantic.BaseModel):
    """An OpenAI message type to send to an LLM
    """
    role: Literal['user', 'system', 'assistant']
    content: str

class GeneratioConfig(pydantic.BaseModel):
    """Configurations to generate text from query results using an LLM

    Args
    ----
    prompt_llm_combo: Literal['vectara-summary-ext-v1.2.0', 'vectara-summary-ext-v1.3.0']
        The name of the prompt-LLM combo to use for generation. Vectara uses a combo of a prompt template and an LLM to let users specify both of them in a single string. If you have custom prompt templates later, the default prompt template associated with the combo will be overwritten by the custom one but the LLM will remain the same -- this is a way to indrectly specify the LLM to use for generation. Default is 'vectara-summary-ext-v1.2.0' which uses GPT-3.5.
        Corresponding to `summarizerPromptName` in Vectara API v1. 

    num_retrieval_results_for_generation: int
        The LLM will generate text from the top `num_retrieval_results_for_generation` results from the retrieval stage. 
        Default is 5.  Corresponding to `maxSummarizedResults` in Vectara API v1.

    output_lang: Literal['auto', 'eng', 'deu', 'fra', 'zho', 'kor', 'ara', 'rus', 'tha', 'nld', 'ita', 'por', 'spa', 'jpn', 'pol', 'tur', 'vie', 'ind', 'ces', 'ukr', 'ell', 'heb', 'fas', 'hin', 'urd', 'swe', 'ben', 'msa', 'ron']
        The language of the generated text. Default is 'eng'. Corresponding to `responseLang` in Vectara API v1.

    prompt_template: str
        
        A prompt template in Apache Velocity format. It is a mixture of control sequences, variables, and OpenAI's Message objects. Default is the empty string meaning that no custom prompt tempalte is used Here is one example: 

        ```
        [
            {"role": "system", "content": "You are a helpful search assistant."},
            #foreach ($qResult in $vectaraQueryResults)
                {"role": "user", "content": "Give me the $vectaraIdxWord[$foreach.index] search result."},
                {"role": "assistant", "content": "${qResult.getText()}" },
            #end
            {"role": "user", "content": "Generate a summary for the query '${vectaraQuery}' based on the above results."}
        ]
        ```

    """
    prompt_llm_combo: Literal[
        'vectara-summary-ext-v1.2.0',  # GPT-3.5 
        'vectara-summary-ext-v1.3.0'   # 
        ] = 'vectara-summary-ext-v1.2.0'
    num_retrieval_results_for_generation: int = 5
    output_lang: Literal['auto', 'eng', 'deu', 'fra', 'zho', 'kor', 'ara', 'rus', 'tha', 'nld', 'ita', 'por', 'spa', 'jpn', 'pol', 'tur', 'vie', 'ind', 'ces', 'ukr', 'ell', 'heb', 'fas', 'hin', 'urd', 'swe', 'ben', 'msa', 'ron'] = 'eng' 
    prompt_template: str= ''

