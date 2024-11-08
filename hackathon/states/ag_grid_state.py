# trunk-ignore-all(ruff/ANN101)
from __future__ import annotations

import reflex as rx

from hackathon.otel import tracer


class AgGridState(rx.State):
    # trunk-ignore-begin(ruff/RUF012)
    default_span_name: str = "ag_grid_state"
    display_data_indices: list[int] = []
    ag_grid_selection_index: int | None = None
    # trunk-ignore-end(ruff/RUF012)

    @rx.var()
    def has_selected_data(
        self,
    ) -> bool:
        return self.ag_grid_selection_index is not None

    def event_selected_ag_grid_row(
        self,
        rows: list[dict[str, str]],
        _0: int,
        _1: int,
    ) -> None:
        del _0, _1, rows
        span_name: str = f"{self.default_span_name}-event_selected_ag_grid_row"
        with tracer.start_as_current_span(span_name) as span:
                span.add_event(
                     name="selected_ag_row",
                     attributes={},
                )
                return
