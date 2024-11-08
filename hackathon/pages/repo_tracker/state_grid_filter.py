# trunk-ignore-all(ruff/ANN10,ruff/ANN101,ruff/RUF012,trunk/ignore-does-nothing)
from __future__ import annotations

from typing import TYPE_CHECKING, Generator

import reflex as rx

from hackathon.app_state import AppState, ClientType
from hackathon.otel import tracer
from hackathon.pages.repo_tracker.state_grid import GridState

if TYPE_CHECKING:
    import chromadb.api.client

from .constants import (
    DEFAULT_DISTANCE_THRESHOLD_FOR_VECTOR_SEARCH,
    NUMBER_OF_RESULTS_TO_DISPLAY_FOR_VECTOR_SEARCH,
)
from .helpers.helper_chroma import chroma_get_projects


class FilterGridState(rx.State):
    default_span_name: str = "filter_grid_state"
    vector_search_distance_threshold: int = DEFAULT_DISTANCE_THRESHOLD_FOR_VECTOR_SEARCH
    vector_search_filter_text_current: str = ""
    vector_search_filter_text_most_recent: str = ""
    repo_path: str = ""

    def repo_path_setter(
        self,
        repo_path: str,
    ) -> Generator[None, None, None]:
        span_name: str = f"{self.default_span_name}-repo_path_setter"
        with tracer.start_as_current_span(span_name) as span:
            self.repo_path = repo_path
            yield

            span.add_event(
                name="repo_path-set",
                attributes={
                    "repo_path": str(self.repo_path),
                },
            )

    def repo_path_reseter(
        self,
    ) -> Generator[None, None, None]:
        span_name: str = f"{self.default_span_name}-repo_path_reseter"
        with tracer.start_as_current_span(span_name) as span:
            self.repo_path = ""
            yield

            span.add_event(
                name="repo_path_current-clear",
            )

    def vector_search_distance_threshold_setter(
        self,
        value: list[int | float],
    ) -> Generator[None, None, None]:
        span_name: str = (
            f"{self.default_span_name}-vector_search_distance_threshold_setter"
        )
        with tracer.start_as_current_span(span_name) as span:
            vector_search_distance_threshold: int | float = value[0]
            self.vector_search_distance_threshold = vector_search_distance_threshold
            yield

            span.add_event(
                name="vector_search_distance_threshold_setter",
                attributes={
                    "vector_search_distance_threshold": vector_search_distance_threshold,
                },
            )

    def vector_search_distance_threshold_commiter(
        self,
        value: list[int],
    ) -> Generator[None, None, None]:
        del value
        span_name: str = (
            f"{self.default_span_name}-vector_search_distance_threshold_commiter"
        )
        with tracer.start_as_current_span(span_name) as span:
            vector_search_distance_threshold: int = (
                self.vector_search_distance_threshold
            )
            self._filter_grid_with_vector_search_distance_threshold(
                vector_search_distance_threshold=vector_search_distance_threshold,
            )
            yield

            span.add_event(
                name="vector_search_distance_threshold-committed",
                attributes={
                    "vector_search_distance_threshold": vector_search_distance_threshold,
                },
            )

    def vector_search_filter_text_setter(
        self,
        vector_search_filter_text_current: str,
    ) -> Generator[None, None, None]:
        span_name: str = f"{self.default_span_name}-vector_search_filter_text_setter"
        with tracer.start_as_current_span(span_name) as span:
            self.vector_search_filter_text_current = vector_search_filter_text_current
            yield

            span.add_event(
                name="vector_search_filter_text-set",
                attributes={
                    "vector_search_filter_text": str(
                        vector_search_filter_text_current,
                    ),
                },
            )
            if not vector_search_filter_text_current:
                return

            self.vector_search_filter_text_most_recent = (
                vector_search_filter_text_current
            )

    def _event_filter_grid(
        self,
        vector_search_distance_threshold: int | None,
        vector_search_filter_text_current: str | None,
        vector_search_filter_text_most_recent: str | None,
    ) -> Generator[None, None, None]:
        span_name: str = f"{self.default_span_name}-event-filter_grid"
        with tracer.start_as_current_span(span_name) as span:
            span.add_event(
                name="filter_grid-queued",
                attributes={  # trunk-ignore(pyright/reportArgumentType)
                    "vector_search_filter_text-most_recent": str(
                        self.vector_search_filter_text_most_recent,
                    ),
                    "vector_search_filter_text-current": vector_search_filter_text_current,
                    "vector_search_distance_threshold": (
                        vector_search_distance_threshold
                        if vector_search_distance_threshold is not None
                        else "None"
                    ),
                },
            )

            def filter_with_vector_search_distance_threshold(
                vector_search_distance_threshold: int,
                vector_search_filter_text_most_recent: str | None,
            ) -> list[int]:
                span.add_event(
                    name="filter_grid-filtering-vector_search_distance_threshold-queued",
                )
                if vector_search_filter_text_most_recent is None:
                    error_msg: str = "vector_search_filter_text_most_recent is None"
                    exception: AssertionError = AssertionError(error_msg)
                    span.record_exception(
                        exception=exception,
                    )
                    raise exception

                span.add_event(
                    name="filter_grid-filtering-vector_search_distance_threshold-started",
                    attributes={
                        "vector_search_distance_threshold": vector_search_distance_threshold,
                        "vector_search_filter_text_most_recent": vector_search_filter_text_most_recent,
                    },
                )
                distance_threshold: float = (
                    FilterGridState.vector_search_distance_threshold / 100
                )
                chroma_client: chromadb.api.ClientAPI = ( # trunk-ignore(pyright/reportAssignmentType)
                    AppState.get_client(
                        client_type=ClientType.CHROMA,
                    )
                )
                chroma_get_projects(
                    repo_filter_vector_search_text=vector_search_filter_text_most_recent,
                    n_results=NUMBER_OF_RESULTS_TO_DISPLAY_FOR_VECTOR_SEARCH,
                    client=chroma_client,
                    distance_threshold=distance_threshold,
                )
                return []  # TODO(elvis): filter with chroma
                # https://elvis.ai

            def filter_with_vector_search_filter_text(
                vector_search_filter_text_current: str,
                # TODO(elvis): add a wrapper for this function that the component can call since it passes in a value
                # https://elvis.ai
            ) -> list[int]:
                span.add_event(
                    name="filter_grid-filtering-vector_search_filter_text",
                    attributes={  # trunk-ignore(pyright/reportArgumentType)
                        "vector_search_filter_text": vector_search_filter_text_current,
                    },
                )
                repo_paths: list[str] = []  # TODO(elvis): Use chroma
                # https://elvis.ai
                return [
                    index
                    for index in (
                        GridState.find_project_index_using_repo_path(
                            projects=AppState.projects,
                            repo_path=repo_path,
                        )
                        for repo_path in repo_paths
                    )
                    if index is not None
                ]

        display_data_indices: list[int] | None = None
        match vector_search_distance_threshold, vector_search_filter_text_current:
            case None, None:
                span.add_event(
                    name="filter_grid-aborted",
                )

            case _, None:
                display_data_indices = filter_with_vector_search_distance_threshold(
                    vector_search_distance_threshold=vector_search_distance_threshold,
                    vector_search_filter_text_most_recent=vector_search_filter_text_most_recent,
                )

            case None, _:
                display_data_indices = filter_with_vector_search_filter_text(
                    vector_search_filter_text_current=vector_search_filter_text_current,
                )

            case _, _:
                span.add_event(
                    name="filter_grid-aborted",
                )
                error_msg: str = (
                    "Cannot filter with both distance threshold and repo paths"
                )
                exception: AssertionError = AssertionError(error_msg)
                span.record_exception(
                    exception=exception,
                )
                raise exception

        GridState.display_data_indices_setter(  # trunk-ignore(pyright/reportCallIssue)
            display_data_indices=display_data_indices,
        )
        yield

        span.add_event(
            name="filter_grid-finished",
            attributes={
                "display_data_indices-length": (
                    len(display_data_indices)
                    if display_data_indices is not None
                    else "None"
                ),
            },
        )
        return

    def _filter_grid_with_vector_search_distance_threshold(
        self,
        vector_search_distance_threshold: int,
    ) -> Generator[None, None, None]:
        span_name: str = (
            f"{self.default_span_name}-event_filter_grid_with_vector_search_distance_threshold"
        )
        with tracer.start_as_current_span(span_name):
            self._event_filter_grid(
                vector_search_distance_threshold=vector_search_distance_threshold,
                vector_search_filter_text_current=None,
                vector_search_filter_text_most_recent=self.vector_search_filter_text_most_recent,
            )
            yield
            return

    def _filter_grid_with_vector_search_filter_text(
        self,
        vector_search_filter_text_current: str,
    ) -> Generator[None, None, None]:
        span_name: str = (
            f"{self.default_span_name}-filter_grid_with_vector_search_filter_text"
        )
        with tracer.start_as_current_span(span_name) as span:
            vector_search_filter_text_most_recent: str = (
                self.vector_search_filter_text_most_recent
            )
            if not vector_search_filter_text_current:
                yield

                span.add_event(
                    name="vector_search_filter_text_current-aborted",
                    attributes={
                        "vector_search_filter_text_most_recent": vector_search_filter_text_most_recent,
                    },
                )
                return

            self._event_filter_grid(
                vector_search_filter_text_current=vector_search_filter_text_current,
                vector_search_filter_text_most_recent=vector_search_filter_text_most_recent,
                vector_search_distance_threshold=None,
            )
            yield

            self.vector_search_filter_text_setter(
                vector_search_filter_text_current=vector_search_filter_text_current,
            )
            return

    def event_filter_grid_with_vector_search_filter_text(
        self,
    ) -> Generator[None, None, None]:
        span_name: str = (
            f"{self.default_span_name}-event_filter_grid_with_vector_search_filter_text"
        )
        with tracer.start_as_current_span(span_name) as span:
            vector_search_filter_text_current: str = (
                self.vector_search_filter_text_current
            )
            self._filter_grid_with_vector_search_filter_text(
                vector_search_filter_text_current=vector_search_filter_text_current,
            )
            yield

            span.add_event(
                name=span_name,
                attributes={
                    "vector_search_filter_text_current": vector_search_filter_text_current,
                },
            )
            return
