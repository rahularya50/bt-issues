from dataclasses import dataclass
from typing import List


@dataclass
class Issue:
    title: str
    status: str
    body: str
    replies: List[str]


@dataclass
class StructuredIssue(Issue):
    build: str
    issue_type: str
    repro_steps: str
    expected: str
    actual: str
    how_often: str
    effect: str
    debug_info: str
    network_operator: str
    sim_operator: str
