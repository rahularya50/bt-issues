from collections import defaultdict
from typing import List, TypeVar

from sklearn.cluster import AgglomerativeClustering  # type: ignore

from embeddings import Embedding
from models import StructuredIssue


def cluster_by_embedding(
    issues: List[StructuredIssue], embeddings: List[Embedding]
) -> None:
    model = AgglomerativeClustering(n_clusters=None, distance_threshold=2)
    model.fit(embeddings)

    clusters = defaultdict(list)
    for issue, label in zip(issues, model.labels_):
        clusters[label].append(issue)

    for i, cluster in clusters.items():
        print("Cluster ", i + 1)
        print([x.issue.title for x in cluster])
        print("")
