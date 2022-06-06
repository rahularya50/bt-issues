from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, TYPE_CHECKING, Union

import numpy as np
import numpy.typing


Embedding = np.typing.NDArray[np.float_]


class BatchEmbedder:
    @dataclass
    class DeferredEmbedding:
        handle: Union["BatchEmbedder", Embedding]

        def get(self) -> Embedding:
            if isinstance(self.handle, BatchEmbedder):
                self.handle._run_batch()
                assert not isinstance(self.handle, BatchEmbedder)
            return self.handle

    if TYPE_CHECKING:
        from sentence_transformers import SentenceTransformer

    model: "SentenceTransformer"
    todo: DefaultDict[str, List[DeferredEmbedding]]

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.todo = defaultdict(list)

    def embed(self, sentence: str) -> DeferredEmbedding:
        out = BatchEmbedder.DeferredEmbedding(self)
        self.todo[sentence].append(out)
        return out

    def _run_batch(self) -> None:
        sentences = list(self.todo.keys())
        embeddings = self.model.encode(sentences)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        for sentence, embedding in zip(sentences, embeddings):
            for deferred in self.todo[sentence]:
                deferred.handle = embedding
        self.todo.clear()
