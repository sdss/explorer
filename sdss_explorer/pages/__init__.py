import solara as sl
from solara import lab  # noqa, save for when 1.28 bug is fixed.
import reacton.ipyvuetify as rv

from .auth import LoginButton
from .state import State
from .dataframe import NoDF
from .sidebar import sidebar
from .grid import ObjectGrid


def create_callable(dataset):
    """Doubly wrapped lambda generator."""
    return lambda: State.load_dataset(dataset)


@sl.component
def Page():
    df = State.df.value

    # PAGE TITLE
    # TODO: make this adaptive in some cool way
    sl.Title("(NOTPUBLIC) SDSS Visboard")
    with sl.AppBar():
        # main title object
        sl.AppBarTitle(children=[rv.Icon(children=["mdi-orbit"]), " SDSS"])

        # dataset selection
        # NOTE: may be moved in future!
        btn = sl.Button(label=State.dataset.value,
                        icon_name="mdi-database",
                        text=True)
        if State.dataset.value is not None:
            with lab.Menu(activator=btn, close_on_content_click=True):
                with sl.Column(gap="0px"):
                    [
                        sl.Button(
                            label=dataset,
                            on_click=create_callable(dataset),
                        ) for dataset in State.datasets
                        if dataset != State.dataset.value
                    ]

        # appbar buttons
        # lab.ThemeToggle()
        sl.Button(icon_name="mdi-wheelchair-accessibility", text=True)
        LoginButton()
    # SIDEBAR
    sidebar()
    # MAIN GRID
    if df is not None:
        ObjectGrid()
    else:
        NoDF()


@sl.component
def Layout(children):
    # route, routes = sl.use_route()

    return sl.AppLayout(sidebar_open=False, children=children, color="purple")


if __name__ == "__main__":
    Layout(Page())
