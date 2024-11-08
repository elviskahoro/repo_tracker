# trunk-ignore-all(ruff/ANN10,ruff/ANN101,ruff/RUF012,trunk/ignore-does-nothing)
from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

import reflex as rx
from sqlalchemy import select

from hackathon import helper_github, helper_perplexity
from hackathon.app_state import AppState, ClientType
from hackathon.models.project import Project
from hackathon.otel import tracer

from .helpers.helper_chroma import chroma_add_project
from .helpers.helper_perplexity import perplexity_get_repo

if TYPE_CHECKING:
    import chromadb.api.client
    import github


class RepoState(rx.State):
    default_span_name: str = "repo_state"

    @rx.background
    async def event_fetch_repo_from_github(
        self,
    ) -> AsyncGenerator[rx.Component | None, None]:
        span_name: str = f"{self.default_span_name}-event_fetch_repo_from_github"
        async with self:
            span = tracer.start_span(span_name)
            repo_path_search: str = helper_github.extract_repo_path_from_url(
                url=self.repo_path,
            )
            client_github: github.Github = AppState.get_client( # trunk-ignore(pyright/reportAssignmentType)
                client_type=ClientType.GITHUB,
            )
            repo: github.Repository | None = helper_github.fetch_repo(
                repo_path=repo_path_search,
                client=client_github,
            )
            if repo is None:
                span_event_name: str = "repo-not_found"
                repo_path: str = self.repo_path
                self.repo_path_reseter()
                span.add_event(
                    name=span_event_name,
                    attributes={
                        "repo_path": repo_path,
                    },
                )
                yield rx.toast.error(
                    message=span_event_name,
                )
                return

            span.add_event(
                name="repo-found",
                attributes={
                    "repo_path": str(repo.full_name),
                    "repo_description": str(repo.description),
                },
            )
            project: Project = Project.from_repo(
                repo=repo,
            )
            span.add_event(
                name="project-created_from_repo",
                attributes={
                    "project_repo_path": str(project.repo_path),
                    "project_stars": str(project.stars),
                    "project_language": str(project.language),
                    "project_website": str(project.website),
                    "project_description": str(project.description),
                    "project_created_at": str(project.created_at),
                },
            )
            self.add_project_to_display_data(project)
            self.repo_path_reseter()
            yield

            perplexity_client: helper_perplexity.Client = AppState.get_client( # trunk-ignore(pyright/reportAssignmentType)
                client_type=ClientType.PERPLEXITY,
            )
            perplexity_description: str | None = await perplexity_get_repo(
                repo_url=project.repo_url,
                client=perplexity_client,
            )
            if perplexity_description is not None:
                project.set_description(
                    description=perplexity_description,
                )
                yield

            for _ in self.save_project(project):
                yield

            chroma_client: chromadb.api.ClientAPI = AppState.get_client( # trunk-ignore(pyright/reportAssignmentType)
                client_type=ClientType.CHROMA,
            )
            chroma_add_project(
                project=project,
                client=chroma_client,
            )
            yield

    def event_on_page_load(
        self,
    ) -> None:
        span_name: str = f"{self.default_span_name}-event_on_page_load"
        with tracer.start_as_current_span(span_name) as span:
            with rx.session() as session:
                AppState.projects = (
                    session.exec(  # trunk-ignore(pyright/reportCallIssue)
                        statement=select(  # trunk-ignore(pyright/reportArgumentType)
                            Project,
                        ),
                    )
                    .scalars()
                    .all()
                )

            span.add_event(
                name="projects-loaded",
                attributes={
                    "project_count": len(AppState.projects),
                },
            )
            self.display_data_indices = list(range(len(AppState.projects)))
