from __future__ import annotations

from typing import TYPE_CHECKING, Generator

from github.GithubException import GithubException

from hackathon import helper_github
from hackathon.otel import tracer

if TYPE_CHECKING:
    from github import Github
    from github.PullRequest import PullRequest
    from github.Repository import Repository


def fetch_repo(
    repo_path: str,
    client: Github | None,
) -> Repository | None:
    with tracer.start_as_current_span("fetch_repo") as span:
        span.add_event(
            name="fetch_repo-started",
            attributes={
                "repo_path": repo_path,
            },
        )
        repo: Repository | None = None
        try:
            client = helper_github.check_client(
                client=client,
            )
            repo = client.get_repo(repo_path)
            span.add_event(
                name="fetch_repo-completed",
                attributes={
                    "repo_path": repo_path,
                    "repo_full_name": repo.full_name,
                },
            )

        except GithubException as e:
            span.add_event(
                name="fetch_repo-error",
                attributes={
                    "repo_path": repo_path,
                },
            )
            span.record_exception(e)

        return repo


def fetch_pull_requests(
    repo: Repository,
) -> Generator[PullRequest, None, None]:
    span_name: str = "fetch_pull_requests"
    with tracer.start_as_current_span(span_name) as span:
        span.add_event(
            name=f"{span_name}-started",
        )
        yield from repo.get_pulls(
            state="all",
            sort="updated",
            direction="desc",
        )

        span.add_event(
            name=f"{span_name}-completed",
        )


def fetch_pull_request_for_repo(
    repo: Repository,
) -> Generator[PullRequest, None, None]:
    span_name: str = "fetch_pull_request_for_repo"
    with tracer.start_as_current_span(span_name) as span:
        span.add_event(
            name=f"{span_name}-started",
        )
        yield from fetch_pull_requests(
            repo=repo,
        )

        span.add_event(
            name=f"{span_name}-completed",
        )
