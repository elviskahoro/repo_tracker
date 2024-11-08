# trunk-ignore-all(pyright/reportArgumentType)
from __future__ import annotations

import reflex as rx
from reflex_ag_grid import ag_grid

from hackathon.models.project import Project
from hackathon.pages.repo_tracker.constants import (
    AG_GRID_ID,
    AG_GRID_THEME,
    DEFAULT_DISTANCE_THRESHOLD_FOR_VECTOR_SEARCH,
    REPO_FILTER_INPUT_ID,
    REPO_SEARCH_INPUT_ID,
    REPO_SIMILARITY_THRESHOLD_MAX,
    REPO_SIMILARITY_THRESHOLD_MIN,
    REPO_SIMILARITY_THRESHOLD_STEP,
)
from hackathon.pages.repo_tracker.state import State
from hackathon.pages.repo_tracker.state_grid_filter import FilterGridState

AG_GRID_COLUMN_DEFINITIONS = Project.get_ag_grid_column_definitions()


def index() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.logo(),
            rx.color_mode.button(),
            margin_y="1em",
            width="100%",
            justify_content="space-between",
        ),
        rx.flex(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.button(
                            "Vector search with filter",
                            on_click=FilterGridState.event_filter_grid_with_vector_search_filter_text,
                            margin_bottom="1em",
                        ),
                        rx.heading(FilterGridState.vector_search_distance_threshold),
                    ),
                    rx.slider(
                        id="distance-threshold-slider",
                        min=REPO_SIMILARITY_THRESHOLD_MIN,
                        max=REPO_SIMILARITY_THRESHOLD_MAX,
                        step=REPO_SIMILARITY_THRESHOLD_STEP,
                        default_value=DEFAULT_DISTANCE_THRESHOLD_FOR_VECTOR_SEARCH,
                        on_change=FilterGridState.vector_search_distance_threshold_setter,
                        on_value_commit=FilterGridState.vector_search_distance_threshold_commiter,
                        width="100%",
                    ),
                ),
            ),
            rx.spacer(),
            rx.input(
                id=REPO_SEARCH_INPUT_ID,
                value=FilterGridState.repo_path,
                placeholder="GitHub repo path e.g. reflex-dev/reflex",
                on_change=FilterGridState.repo_path_setter,
                width="40%",
            ),
            rx.button(
                "Fetch repo data",
                on_click=State.event_github_repo_getter,
                margin_bottom="1em",
            ),
            justify_content="space-between",
            width="100%",
        ),
        rx.hstack(
            rx.vstack(
                rx.text_area(
                    id=REPO_FILTER_INPUT_ID,
                    value=FilterGridState.vector_search_filter_text_current,
                    placeholder="Search keywords in repo description",
                    on_change=FilterGridState.vector_search_filter_text_setter,
                    width="100%",
                    min_width="380px",
                    height="100%",
                    min_height="100px",
                    resize="horizontal",
                ),
            ),
            rx.spacer(),
            rx.fragment(FilterGridState.repo_card_stats),
            rx.fragment(FilterGridState.repo_card_description),
            width="100%",
        ),
        ag_grid(
            id=AG_GRID_ID,
            column_defs=AG_GRID_COLUMN_DEFINITIONS,
            row_data=FilterGridState.display_data,
            pagination=True,
            pagination_page_size=100,
            pagination_page_size_selector=[
                50,
                100,
            ],
            on_selection_changed=FilterGridState.event_selected_ag_grid_row,
            theme=AG_GRID_THEME,
            width="100%",
            height="60vh",
        ),
        width="80%",
        margin="0 auto",
        spacing="4",
    )
