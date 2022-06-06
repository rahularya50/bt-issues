import pickle
from multiprocessing.pool import ThreadPool
from typing import Callable, List, Optional, Tuple, TypeVar, Union

import click
from click import Command, Group
from tqdm import tqdm
from typing_extensions import reveal_type

from decodables import IssueLink, IssuePage
from decoder_core import MatchFailure
from embeddings import BatchEmbedder, Embedding
from fetchers import fetch_issue, fetch_page
from knn import cluster_by_embedding
from models import Issue, StructuredIssue


def get_issue(issue_link: IssueLink) -> Issue:
    issue = fetch_issue(issue_link.issue_id)
    try:
        decoded_page = IssuePage.decode(issue)
    except MatchFailure:
        print(issue)
        raise
    issue = Issue(issue_link.issue_id, decoded_page)
    return issue


T = TypeVar("T")
U = TypeVar("U")


def stage(
    group: Group, src: Union[str, T], sink: Optional[str] = None
) -> Callable[[Callable[[T], U]], Command]:
    def decorator(f: Callable[[T], U]) -> Command:
        def wrapped() -> None:
            with open(f"{src}.pickle", "rb") as g:
                data: T = pickle.load(g)
            out: U = f(data)
            if sink is not None:
                with open(f"{sink}.pickle", "wb") as g:
                    pickle.dump(out, g)

        wrapped.__name__ = f.__name__
        return group.command(wrapped)

    return decorator


@click.group(chain=True)
def cli() -> None:
    pass


@stage(cli, None, "issues")
def fetch_issues(_: None) -> List[Issue]:
    page = fetch_page("bluetooth", 1, num_results=256)
    with ThreadPool(8) as p:
        issues = list(tqdm(p.imap(get_issue, page.links), total=len(page.links)))
    return issues


@stage(cli, "issues", "structured_issues")
def structure_issues(issues: List[Issue]) -> List[StructuredIssue]:
    structured_issues = [
        x for x in [issue.try_structured() for issue in issues] if x is not None
    ]
    for x in structured_issues:
        print(x.issue.id)
        print(x)
    return structured_issues


@stage(cli, "structured_issues", "embedded_issues")
def classify_issues(
    structured_issues: List[StructuredIssue],
) -> Tuple[List[StructuredIssue], List[Embedding]]:
    batch_embedder = BatchEmbedder()
    deferred_embedded_titles = [
        batch_embedder.embed(issue.structured_fields[StructuredIssue.FIELD_STEPS])
        for issue in structured_issues
    ]
    deferred_embedded_steps = [
        batch_embedder.embed(issue.structured_fields[StructuredIssue.FIELD_STEPS])
        for issue in structured_issues
    ]
    embeddings = [
        e1.get() + e2.get()
        for e1, e2 in zip(deferred_embedded_titles, deferred_embedded_steps)
    ]
    return structured_issues, embeddings


@stage(cli, "embedded_issues", None)
def cluster_issue_titles(
    issue_embeddings: Tuple[List[StructuredIssue], List[Embedding]]
) -> None:
    issues, embeddings = issue_embeddings
    cluster_by_embedding(issues, embeddings)


if __name__ == "__main__":
    cli()
