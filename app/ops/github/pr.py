# %%
import os
from datetime import date

import requests
import typer
from dotenv import load_dotenv

load_dotenv("./.env")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = os.environ["OWNER"]
REPO = os.environ["REPO"]

BASE_URL = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_pr_contents(url: str):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def _parse_iso_date(param_name: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(
            f"{value!r} is not a valid ISO date (YYYY-MM-DD).",
            param_name=param_name,
        ) from exc


def main(
    per_page: int = typer.Option(
        10,
        "--per-page",
        "-p",
        min=1,
        max=100,
        help="Number of PRs to request per page (GitHub maximum is 100).",
    ),
    start: str = typer.Option(
        "2025-01-01",
        "--start",
        "-s",
        help="Start date (YYYY-MM-DD) for the PR search range.",
    ),
    end: str | None = typer.Option(
        None,
        "--end",
        "-e",
        help="End date (YYYY-MM-DD) for the PR search range. Defaults to today.",
        show_default="today",
    ),
):
    start_date = _parse_iso_date("start", start)
    end_date = date.today() if end is None else _parse_iso_date("end", end)
    if start_date > end_date:
        raise typer.BadParameter(
            "Start date must be earlier than or equal to end date.",
            param_name="start",
        )

    start_param = start_date.isoformat()
    end_param = end_date.isoformat()

    base_url = (
        f"{BASE_URL}/search/issues?"
        f"q=repo:{OWNER}/{REPO}+type:pr+created:{start_param}..{end_param}+state:closed"
        f"&per_page={per_page}"
    )
    url = f"{base_url}&page=1"

    issues = fetch_pr_contents(url=url)
    n = len(issues["items"])

    def to_pr_urls(issues: dict) -> list[str]:
        return [itm["pull_request"]["url"] for itm in issues["items"]]

    pr_list = to_pr_urls(issues)
    page = 1
    while n == per_page:
        page += 1
        url = f"{base_url}&page={page}"
        issues = fetch_pr_contents(url=url)
        n = len(issues["items"])
        pr_list.extend(to_pr_urls(issues))

    # %%
    pr_records = []
    review_records = []
    comment_records = []
    commit_records = []

    for pr_url in pr_list:
        print(pr_url)

        # PR
        pr = fetch_pr_contents(url=pr_url)
        pr_created_at = pr["created_at"]
        pr_updated_at = pr["updated_at"]

        # レビュー
        url = pr_url + "/reviews"
        reviews = fetch_pr_contents(url=url)
        prev_at = pr_created_at
        for itm in reviews:
            item_id = itm["id"]
            state = itm["state"]
            user = itm["user"]["login"]
            user_type = itm["user"]["type"]
            submitted_at = itm["submitted_at"]
            rec = (
                pr_url,
                "REVIEW",
                item_id,
                state,
                user,
                user_type,
                prev_at,
                submitted_at,
            )
            # print("REVIEW:", item_id, state, user, user_type, prev_at, submitted_at)
            prev_at = submitted_at
            review_records.append(rec)

        # コメント
        url = pr_url + "/comments"
        comments = fetch_pr_contents(url=url)
        for itm in comments:
            item_id = itm["id"]
            user = itm["user"]["login"]
            user_type = itm["user"]["type"]
            created_at = itm["created_at"]
            updated_at = itm["updated_at"]
            commit_id = itm["commit_id"]
            # print("COMMENT:", commit_id)
            rec = (
                pr_url,
                "COMMENT",
                item_id,
                user,
                user_type,
                created_at,
                updated_at,
                commit_id,
                itm["body"],
            )
            comment_records.append(rec)
        # コミット
        url = pr_url + "/commits"
        commits = fetch_pr_contents(url=url)
        for itm in commits:
            item_id = itm["sha"]
            user = itm["commit"]["committer"]["name"]
            # email = itm["commit"]["author"]["email"]
            n_comments = itm["commit"]["comment_count"]
            message = itm["commit"]["message"]
            user_type = itm["author"]["type"]
            created_at = itm["commit"]["committer"]["date"]
            # print("COMMIT:", item_id, n_comments)
            rec = (
                pr_url,
                "COMMIT",
                item_id,
                user,
                user_type,
                created_at,
                n_comments,
                message,
            )
            commit_records.append(rec)

        pr_rec = (
            pr_url,
            pr_created_at,
            pr_updated_at,
            len(reviews),
            len(commits),
            len(comments),
        )
        pr_records.append(pr_rec)

    # %%
    import pandas as pd

    df_pr = pd.DataFrame(
        pr_records,
        columns=[
            "pr_url",
            "created_at",
            "updated_at",
            "n_reviews",
            "n_commits",
            "n_comments",
        ],
    )
    df_review = pd.DataFrame(
        review_records,
        columns=[
            "pr_url",
            "type",
            "item_id",
            "state",
            "user",
            "user_type",
            "prev_at",
            "submitted_at",
        ],
    )
    df_comment = pd.DataFrame(
        comment_records,
        columns=[
            "pr_url",
            "type",
            "item_id",
            "user",
            "user_type",
            "created_at",
            "updated_at",
            "commit_id",
            "body",
        ],
    )
    df_commit = pd.DataFrame(
        commit_records,
        columns=[
            "pr_url",
            "type",
            "item_id",
            "user",
            "user_type",
            "created_at",
            "n_comments",
            "message",
        ],
    )

    # %%
    import pathlib

    data_dir = pathlib.Path("./data/github/api")
    data_dir.mkdir(parents=True, exist_ok=True)

    # %%
    print("Saving data to TSV files...")
    df_pr.to_csv(data_dir / "pr.tsv", index=False, sep="\t")
    df_review.to_csv(data_dir / "review.tsv", index=False, sep="\t")
    df_comment.to_csv(data_dir / "comment.tsv", index=False, sep="\t")
    df_commit.to_csv(data_dir / "commit.tsv", index=False, sep="\t")


if __name__ == "__main__":
    typer.run(main)
