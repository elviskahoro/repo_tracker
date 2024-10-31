from typing import Callable

import reflex as rx


def index(
    placeholder_function: Callable[[], None],
) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(
                "Hackathon Project Tracker",
                font_size="2em",
            ),
            rx.spacer(),
            rx.color_mode.button(),
            margin_y="1em",
            width="100%",
        ),
        rx.logo(),
        rx.button(
            "Fetch Latest Data",
            on_click=placeholder_function,
        ),
    )
