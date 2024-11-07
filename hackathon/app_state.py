# trunk-ignore-all(ruff/ANN101,ruff/PLW0603,trunk/ignore-does-nothing)
from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Generator

import reflex as rx

from hackathon import helper_chroma, helper_github, helper_perplexity
from hackathon.models.project import Project  # trunk-ignore(ruff/TCH001)
from hackathon.otel import tracer
from hackathon.tokens import TOKENS

if TYPE_CHECKING:
    import chromadb.api.client
    import github
    from sqlalchemy.orm import Session

chroma_client: chromadb.api.ClientAPI | None = None
github_client: github.Github | None = None
perplexity_client: helper_perplexity.Client | None = None

class ClientType(Enum):
    CHROMA = auto()
    GITHUB = auto()
    PERPLEXITY = auto()


class AppState(rx.State):
    # trunk-ignore-begin(ruff/RUF012)
    projects: list[Project] = []
    projects_to_commit: list[Project] = []
    # trunk-ignore-end(ruff/RUF012)

    @staticmethod
    def get_client( # trunk-ignore(ruff/ANN205)
        client_type: ClientType,
    ):
        global chroma_client, github_client, perplexity_client
        match client_type:
            case ClientType.CHROMA:
                if chroma_client := chroma_client:
                    return chroma_client

                chroma_client = helper_chroma.set_up_client_from_tokens(
                    tokens=TOKENS,
                )
                return chroma_client

            case ClientType.GITHUB:
                if github_client := github_client:
                    return github_client

                github_client = helper_github.set_up_client_from_tokens(
                    tokens=TOKENS,
                )
                return github_client

            case ClientType.PERPLEXITY:
                if perplexity_client := perplexity_client:
                    return perplexity_client

                perplexity_client = helper_perplexity.set_up_client_from_tokens(
                    tokens=TOKENS,
                )
                return perplexity_client

        error_msg: str = "ClientType could not be matched"
        raise ValueError(error_msg)


    def _save_projects_to_db(
        self,
        projects: list[Project],
    ) -> Generator[None, None, None]:
        def filter_projects_to_save(
            db: Session,
            projects: list[Project],
        ) -> list[Project]:
            span_name: str = f"{self.default_span_name}-event_get_new_projects"
            with tracer.start_as_current_span(span_name) as span:
                span.add_event(
                    name="get_new_projects-started",
                    attributes={
                        "project_count-to_commit": len(projects),
                    },
                )
                existing_repo_paths: set[str] = {
                    str(path[0])
                    for path in db.query(  # trunk-ignore(pyright/reportCallIssue)
                        Project.repo_path,  # trunk-ignore(pyright/reportArgumentType)
                    ).all()
                }
                span.add_event(
                    name="get_new_projects-existing_repo_paths",
                    attributes={
                        "existing_repo_paths": str(existing_repo_paths),
                        "existing_repo_path_count": len(existing_repo_paths),
                        "existing_repo_path_type": str(type(existing_repo_paths)),
                    },
                )
                new_projects: list[Project] = [
                    project
                    for project in projects
                    if str(project.repo_path) not in existing_repo_paths
                ]
                span.add_event(
                    name="get_new_projects-completed",
                    attributes={
                        "project_count-to_save": len(new_projects),
                    },
                )
                return new_projects

        span_name: str = f"{self.default_span_name}-event_save_projects_to_db"
        with tracer.start_as_current_span(span_name) as span, rx.session() as session:
            if not projects:
                span.add_event(
                    name="db-projects-no_projects_to_save",
                )
                yield

                return

            projects_to_save: list[Project] = filter_projects_to_save(
                db=session,
                projects=projects,
            )
            span.add_event(
                name="db-projects-projects_to_save",
                attributes={
                    "project_count": len(projects_to_save),
                },
            )
            if len(projects_to_save) == 0:
                span.add_event(
                    name="db-projects-no_new_projects_to_save",
                )
                if projects:
                    first_repo, *_ = projects
                    span.add_event(
                        name="db-projects-repo_already_saved",
                        attributes={
                            "repo_path": str(first_repo.repo_path),
                        },
                    )

                yield

                return

            session.bulk_save_objects(projects_to_save)
            session.commit()
            span.add_event(
                name="db-projects-added_to_db",
                attributes={
                    "project_count": len(projects_to_save),
                },
            )
            yield

    def save_project(
        self,
        project: Project,
    ) -> Generator[None, None, None]:
        span_name: str = f"{self.default_span_name}-event_save_project"
        with tracer.start_as_current_span(span_name) as span:
            AppState.projects_to_commit.append(project)
            span.add_event(
                name="projects_to_commit-added_project",
                attributes={
                    "project_repo_path": str(project.repo_path),
                },
            )
            yield from self._save_projects_to_db(
                projects=AppState.projects_to_commit,
            )

            span.add_event(
                name="projects_to_commit-saved_to_db",
            )
            AppState.projects_to_commit.clear()
            span.add_event(
                name="projects_to_commit-cleared",
            )
