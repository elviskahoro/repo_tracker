# trunk-ignore-all(ruff/ANN101,trunk/ignore-does-nothing)
from __future__ import annotations

from typing import Generator

import reflex as rx

from hackathon.app_state import AppState
from hackathon.models import Project  # trunk-ignore(ruff/TCH001)
from hackathon.otel import tracer
from hackathon.states.ag_grid_state import AgGridState

from .components.repo_cards import (
    repo_card_description_component,
    repo_card_skeleton,
    repo_card_stats_component,
)
from .constants import (
    NUMBER_OF_WORDS_TO_DISPLAY_FOR_REPO_DESCRIPTION,
)


class GridState(AgGridState):

    @staticmethod
    def find_project_index_using_repo_path(
        projects: list[Project],
        repo_path: str | None,
    ) -> int | None:
        if repo_path is None:
            return None

        first_index = next(
            (i for i in range(len(projects)) if projects[i].repo_path == repo_path),
            None,
        )
        if first_index is None:
            return None

        return first_index

    @rx.var(
        cache=True,
    )
    def display_data(
        self,
    ) -> list[dict]:
        return [
            AppState.projects[i].to_ag_grid_dict() for i in self.display_data_indices
        ]

    @rx.var
    def ag_grid_selection_repo_path(
        self,
    ) -> str:
        return ""

    def display_data_indices_setter(
        self,
        display_data_indices: list[int],
    ) -> None:
        span_name: str = "event_display_data_indices_setter"
        with tracer.start_as_current_span(span_name) as span:
            self.display_data_indices = display_data_indices
            span.add_event(
                name="display_data_indices-set",
                attributes={
                    "display_data_indices": str(self.display_data_indices),
                },
            )

    def event_selected_ag_grid_row(
        self,
        rows: list[dict[str, str]],
        _0: int,
        _1: int,
    ) -> None:
        del _0, _1
        span_name: str = f"{self.default_span_name}-event_selected_ag_grid_row"
        with tracer.start_as_current_span(span_name) as span:
            if rows and (repo_path := rows[0].get("repo_path")):
                self.ag_grid_selection_index = (
                    GridState.find_project_index_using_repo_path(
                        projects=AppState.projects,
                        repo_path=repo_path,
                    )
                )
                span.add_event(
                    name="selection_repo_path-set",
                    attributes={
                        "repo_path": str(repo_path),
                    },
                )
                return

            span.add_event(
                name="selection_repo_path-unset",
            )

    def add_project_to_display(
        self,
        project: Project,
    ) -> Generator[None, None, None]:
        span_name: str = "add_project_to_display"
        with tracer.start_as_current_span(span_name) as span:

            def append_project() -> int:
                span.add_event(
                    name="add_project-started",
                    attributes={
                        "project_repo_path": str(project.repo_path),
                    },
                )
                AppState.projects.append(project)
                project_index = GridState.find_project_index_using_repo_path(
                    projects=AppState.projects,
                    repo_path=project.repo_path,
                )
                if project_index is None:
                    error_msg: str = (
                        f"Project should be non null and found in projects: {project.repo_path}"
                    )
                    raise AssertionError(error_msg)

                return project_index

            def get_or_append_new_project() -> int:
                project_index: int | None = (
                    GridState.find_project_index_using_repo_path(
                        projects=AppState.projects,
                        repo_path=project.repo_path,
                    )
                )
                span.add_event(
                    name="find_index-completed",
                    attributes={
                        "project_repo_path": str(project.repo_path),
                        "project_index": str(project_index),
                    },
                )
                if project_index is not None:
                    return project_index

                span.add_event(
                    name="add_project-queued",
                    attributes={
                        "project_repo_path": str(project.repo_path),
                    },
                )
                project_index = append_project()
                span.add_event(
                    name="add_project-completed",
                    attributes={
                        "project_repo_path": str(project.repo_path),
                    },
                )
                project_index = GridState.find_project_index_using_repo_path(
                    projects=AppState.projects,
                    repo_path=project.repo_path,
                )
                if project_index is None:
                    error_msg: str = "Project index should be non-null after append"
                    exception: AssertionError = AssertionError(error_msg)
                    span.record_exception(
                        exception=exception,
                    )
                    raise exception

                return project_index

            project_index: int = get_or_append_new_project()
            display_data_indices: list[int] = [*self.display_data_indices]
            span.add_event(
                name="display_data_indices-current",
                attributes={
                    "display_data_indices": str(display_data_indices),
                },
            )
            if project_index in display_data_indices:
                yield

                span.add_event(
                    name="project-already_in_display_data",
                    attributes={
                        "project_repo_path": str(project.repo_path),
                    },
                )
                return

            display_data_indices.append(project_index)
            self.display_data_indices_setter(
                display_data_indices=display_data_indices,
            )
            yield

            span.add_event(
                name="project-added_to_display_data",
                attributes={
                    "project_repo_path": str(project.repo_path),
                },
            )

    @rx.var
    def ui_repo_card_stats(
        self,
    ) -> rx.Component:
        project_index: int | None = GridState.find_project_index_using_repo_path(
            projects=AppState.projects,
            repo_path=self.ag_grid_selection_repo_path,
        )
        if project_index is None:
            return rx.fragment(repo_card_skeleton())

        project: Project = AppState.projects[project_index]
        return rx.fragment(
            repo_card_stats_component(
                repo_path=project.repo_path,
                repo_url=f"https://github.com/{project.repo_path}",
                stars=f"{project.stars:,}",
                language=f"{project.language}",
                website_url=f"{project.website}",
            ),
        )

    @rx.var
    def ui_repo_card_description(
        self,
    ) -> rx.Component:
        project_index: int | None = GridState.find_project_index_using_repo_path(
            projects=AppState.projects,
            repo_path=self.ag_grid_selection_repo_path,
        )
        if project_index is None:
            return rx.fragment(
                repo_card_skeleton(),
            )

        project: Project = AppState.projects[project_index]
        description: str = str(project.description)
        if first_n_words_from_description := " ".join(
            project.description.split()[
                :NUMBER_OF_WORDS_TO_DISPLAY_FOR_REPO_DESCRIPTION
            ],
        ):
            description = first_n_words_from_description

        return rx.fragment(
            repo_card_description_component(
                description=description,
            ),
        )
