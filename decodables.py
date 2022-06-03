from dataclasses import dataclass
from typing import List, Optional, Union

from decoder_core import (
    Decodable,
    INT,
    ListOf,
    NONE,
    OneOf,
    REST,
    SKIP,
    STR,
    Shape,
    match_check,
    match_instance,
)


@dataclass
class IssueLink(Decodable):
    PATTERN = Shape(INT, REST)

    issue_id: int


@dataclass
class SearchPage(Decodable):
    PATTERN = Shape(Shape("b.IssueSearchResponse", ListOf(IssueLink), REST))

    links: List[IssueLink]

    def __init__(self, *links: IssueLink):
        self.links = list(links)


@dataclass
class IssueTitleEvent(Decodable):
    PATTERN = Shape(
        "b.EventDiff",
        "title",
        "Title",
        SKIP * 3,
        Shape(
            NONE,
            Shape(NONE, STR),
        ),
    )

    title: str


@dataclass
class IssueStatusEvent(Decodable):
    PATTERN = Shape(
        "b.EventDiff",
        "status",
        "Status",
        SKIP * 3,
        Shape(
            NONE,
            Shape(NONE, STR),
        ),
    )

    status: str


@dataclass
class IssueComment(Decodable):
    PATTERN = Shape("b.IssueComment", SKIP * 6, STR, REST)
    body: str


@dataclass
class IssueTitleMessage(Decodable):
    PATTERN = Shape(
        "b.IssueEvent",
        SKIP * 2,
        ListOf(
            OneOf(
                IssueTitleEvent,
                IssueStatusEvent,
                SKIP,
            ),
        ),
        SKIP * 2,
        IssueComment,
        REST,
    )

    title: IssueTitleEvent
    status: IssueStatusEvent
    body: IssueComment

    def __init__(
        self,
        title: Optional[IssueTitleEvent] = None,
        status: Optional[IssueStatusEvent] = None,
        body: Optional[IssueComment] = None,
    ):
        self.title = match_instance(title, IssueTitleEvent)
        self.status = match_instance(status, IssueStatusEvent)
        self.body = match_instance(body, IssueComment)


@dataclass
class IssueReplyMessage(Decodable):
    PATTERN = ListOf(OneOf(IssueComment, SKIP))

    comments: List[str]

    def __init__(self, *comments: str):
        match_check(bool(comments), "replies must have at least one comment")
        self.comments = list(comments)


@dataclass
class IssuePage(Decodable):
    PATTERN = Shape(
        Shape(
            "b.ListIssueEventsResponse",
            ListOf(
                OneOf(
                    IssueTitleMessage,
                    IssueReplyMessage,
                    SKIP,
                )
            ),
        )
    )

    title: IssueTitleMessage
    replies: List[IssueReplyMessage]

    def __init__(self, *events: Union[IssueTitleMessage, IssueReplyMessage]):
        has_title = False
        self.replies = []
        for event in events:
            if isinstance(event, IssueTitleMessage):
                match_check(not has_title, "duplicate titles found")
                self.title = event
                has_title = True
            else:
                self.replies.append(event)
        match_check(has_title, "title not found")
