# trunk-ignore-all(trunk/ignore-does-nothing)
import reflex as rx

from .app_style import Style as AppStyle
from .pages.repo_tracker.page import index
from .pages.repo_tracker.state_repo import RepoState

APP_STYLE: AppStyle = AppStyle()

app = rx.App(
    style=APP_STYLE.dark,
    theme=rx.theme(
        has_background=True,
        radius="large",
        accent_color="teal",
    ),
)
app.add_page(
    component=index,
    route="/",
    on_load=RepoState.event_on_page_load, # trunk-ignore(pyright/reportArgumentType)
)
