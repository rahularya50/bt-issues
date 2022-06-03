from decodables import IssuePage
from fetchers import fetch_issue, fetch_page


def main() -> None:
    page = fetch_page("bluetooth", 1, num_results=4)
    for issue_link in page.links:
        issue = fetch_issue(issue_link.issue_id)
        print(issue_link.issue_id)
        print(IssuePage.decode(issue))


if __name__ == "__main__":
    main()
