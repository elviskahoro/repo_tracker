from __future__ import annotations

import re
from typing import TYPE_CHECKING, Generator

from github import Github
from github.GithubException import GithubException

from hackathon_project_tracker import helper_utils
from hackathon_project_tracker.helper_logging import Severity, log
from hackathon_project_tracker.otel import tracer

if TYPE_CHECKING:
    from github.PullRequest import PullRequest
    from github.Repository import Repository


GITHUB_REPO_PARSER_REGEX: re.Pattern = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
)

def set_up_client_from_tokens(
    tokens: dict[
        str,
        str | None,
    ],
) -> Github | None:
    with tracer.start_as_current_span("set_up_client_from_tokens") as span:
        tokens = helper_utils.check_tokens(
            tokens=tokens,
        )
        log(
            the_log="Setting up client",
            severity=Severity.DEBUG,
            file=__file__,
        )
        github_owner: str | None = tokens.get(
            "GITHUB_OWNER",
            None,
        )
        if github_owner is None:
            span.add_event(
                name="missing_tokens-github",
                attributes={
                    "missing_token": "GITHUB_OWNER",
                },
            )
            return None

        github_repo: str | None = tokens.get(
            "GITHUB_REPO",
            None,
        )
        if github_repo is None:
            span.add_event(
                name="missing_tokens-github",
                attributes={
                    "missing_token": "GITHUB_REPO",
                },
            )
            return None

        github_client_id: str | None = tokens.get(
            "GITHUB_CLIENT_ID",
            None,
        )
        if github_client_id is None:
            span.add_event(
                name="missing_tokens-github",
                attributes={
                    "missing_token": "GITHUB_CLIENT_ID",
                },
            )
            return None

        github_client_secret: str | None = tokens.get(
            "GITHUB_CLIENT_SECRET",
            None,
        )
        if github_client_secret is None:
            span.add_event(
                name="missing_tokens-github",
                attributes={
                    "missing_token": "GITHUB_CLIENT_SECRET",
                },
            )
            return None

        github_client: Github = Github()
        github_client.get_oauth_application(
            client_id=github_client_id,
            client_secret=github_client_secret,
        )
        return github_client


def extract_repo_path_from_url(
    url: str,
) -> str:
    match: re.Match | None = GITHUB_REPO_PARSER_REGEX.match(url)
    if match is None:
        error_message: str = "Invalid GitHub URL format. Expected format: owner/repo"
        raise ValueError(error_message)

    return match.group("owner") + "/" + match.group("repo")


def check_client(
    client: Github | None,
) -> Github:
    with tracer.start_as_current_span("check_client") as span:
        span.add_event(
            name="check_client-started",
        )
        if client is None:
            error_message: str = "Client is required"
            exception: AssertionError = AssertionError(error_message)
            span.record_exception(exception)
            span.add_event(
                name="check_client-error",
            )
            raise exception

        return client


def fetch_repo(
    repo_path: str,
    client: Github,
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
            client = check_client(
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
            span.record_exception(e)
            span.add_event(
                name="fetch_repo-error",
                attributes={
                    "repo_path": repo_path,
                },
            )

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
