from __future__ import annotations

import reflex as rx

from .constants import REPO_STATS_CARD_SIZE


def repo_stats(
    repo_path: str,
    repo_url: str,
    stars: str,
    language: str,
    website: str,
    website_url: str,
) -> rx.Component:
    return rx.card(
        rx.data_list.root(
            rx.data_list.item(
                rx.data_list.label("Repo"),
                rx.data_list.value(
                    rx.link(
                        repo_path,
                        href=repo_url,
                    ),
                ),
            ),
            rx.data_list.item(
                rx.data_list.label("Stars"),
                rx.data_list.value(stars),
            ),
            rx.data_list.item(
                rx.data_list.label("Language"),
                rx.data_list.value(language),
            ),
            rx.data_list.item(
                rx.data_list.label("Website"),
                rx.data_list.value(
                    rx.link(
                        website,
                        href=website_url,
                    ),
                ),
            ),
            size="1",
        ),
        size=REPO_STATS_CARD_SIZE,
        min_width="100px",
    )
