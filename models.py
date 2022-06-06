from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional

from decodables import IssuePage


@dataclass
class Issue:
    id: int
    title: str
    status: str
    body: str
    replies: List[str]

    def __init__(self, issue_id: int, page: IssuePage) -> None:
        self.id = issue_id
        self.title = page.title.title.title
        self.status = page.title.status.status
        self.body = page.title.body.body
        self.replies = [
            "\n".join(comment.body for comment in reply.comments)
            for reply in page.replies
        ]

    def try_structured(self) -> Optional["StructuredIssue"]:
        field_starts = []
        for field in StructuredIssue.FIELDS:
            prompt_pos = self.body.find(field.prompt)
            if prompt_pos == -1:
                if field.optional:
                    continue
                else:
                    return None
            field_starts.append((field, prompt_pos))

        out = {}
        for i, (field, start_pos) in enumerate(field_starts):
            if i + 1 == len(field_starts):
                succ_pos = len(self.body)
            else:
                succ_pos = field_starts[i + 1][1]
            if succ_pos < start_pos:
                return None
            out[field] = self.body[start_pos + len(field.prompt) : succ_pos]
        return StructuredIssue(self, out)


@dataclass(frozen=True)
class StructuredField:
    name: str
    prompt: str
    optional: bool = False


@dataclass
class StructuredIssue:
    FIELDS: ClassVar[List[StructuredField]] = [
        FIELD_BUILD := StructuredField("build", "Build Number:"),
        FIELD_ISSUE := StructuredField(
            "issue_type", "What type of Android issue is this?"
        ),
        FIELD_STEPS := StructuredField(
            "steps", "What steps would let us observe this issue?"
        ),
        FIELD_EXPECTED := StructuredField("expected", "What did you expect to happen?"),
        FIELD_ACTUAL := StructuredField("actual", "What actually happened?"),
        FIELD_FREQUENCY := StructuredField("frequency", "How often has this happened?"),
        FIELD_EFFECT := StructuredField(
            "effect",
            "What was the effect of this issue on your device usage, such as lost time or work?",
        ),
        FIELD_NOTES := StructuredField("notes", "Additional comments", optional=True),
        FIELD_DEBUG_INFO := StructuredField("debug_info", "Debugging information"),
        FIELD_NETWORK_OPERATOR := StructuredField(
            "network_operator", "Network operator:"
        ),
        FIELD_SIM_OPERATOR := StructuredField("sim_operator", "SIM operator:"),
    ]
    issue: Issue
    structured_fields: Dict[StructuredField, str]

    def __str__(self) -> str:
        out = []
        for field, val in self.structured_fields.items():
            out.append(f"{field.name.title()}: {repr(val)}")
        return "\n".join(out)
