from __future__ import annotations

import re

from github import Github

from hackathon import helper_utils
from hackathon.helper_logging import Severity, log
from hackathon.otel import tracer

GITHUB_REPO_PARSER_REGEX: re.Pattern = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
)

def extract_repo_path_from_url(
    url: str,
) -> str:
    match: re.Match | None = GITHUB_REPO_PARSER_REGEX.match(url)
    if match is None:
        return url

    return match.group("owner") + "/" + match.group("repo")

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


