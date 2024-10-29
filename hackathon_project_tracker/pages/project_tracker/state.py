from __future__ import annotations

from typing import Generator

import reflex as rx
from github import Github
from sqlalchemy import select

from hackathon_project_tracker.models.project import Project
from hackathon_project_tracker.otel import tracer
from hackathon_project_tracker.pages.project_tracker import helper_github
from hackathon_project_tracker.tokens import TOKENS

GITHUB_CLIENT: Github = helper_github.set_up_client_from_tokens(
    tokens=TOKENS,
)
GITHUB_REPO_PATH_DEFAULT: str = helper_github.create_repo_path(
    tokens=TOKENS,
)


class State(rx.State):
    """The state for the project tracker page."""

    current_repo_path: str = GITHUB_REPO_PATH_DEFAULT

    def on_load(
        self: State,
    ) -> None:
        with tracer.start_as_current_span("on_load"), rx.session() as session:
            self.projects = (
                session.exec( # trunk-ignore(pyright/reportCallIssue)
                    statement=select(Project), # trunk-ignore(pyright/reportArgumentType)
                )
                .scalars()
                .all()
            )

    def save_projects(
        self: State,
        projects: list[Project],
    ) -> Generator[None, None, None]:
        with (
            tracer.start_as_current_span(
                "save_projects",
            ) as span,
            rx.session() as session,
        ):
            if not projects:
                span.add_event(
                    name="projects-not_saved",
                )
                return

            session.add_all(projects)
            session.commit()
            yield from (session.refresh(project) for project in projects)

            span.add_event(
                name="projects-saved",
                attributes={
                    "project_count": len(projects),
                },
            )

    def placeholder_function(
        self: State,
    ) -> None:
        with tracer.start_as_current_span("placeholder_function"):
            print("placeholder_function")
