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
    index: bool = False