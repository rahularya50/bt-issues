import json

import requests

from decodables import SearchPage


def clean_reply(reply: str) -> object:
    return json.loads(reply.removeprefix(")]}'"))


def fetch_page(query: str, page_num: int, *, num_results: int = 25) -> SearchPage:
    page = requests.post(
        f"https://issuetracker.google.com/action/issues/list",
        params={"enable_jspb": True},
        json=[query, num_results, None, page_num],
    ).text
    return SearchPage.decode(json.loads(page.removeprefix(")]}'")))


def fetch_issue(issue_id: int) -> object:
    return clean_reply(
        requests.get(
            f"https://issuetracker.google.com/action/issues/{issue_id}/events",
            params={"enable_jspb": True},
        ).text
    )
