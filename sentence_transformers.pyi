from typing import List

import numpy as np


class SentenceTransformer:
    def __init__(self, name: str) -> None:
        ...

    def encode(self, sentences: List[str]) -> List[np.typing.NDArray[np.float_]]:
        ...
