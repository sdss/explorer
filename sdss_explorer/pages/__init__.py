import solara as sl
from solara import lab  # noqa, save for when 1.28 bug is fixed.
import reacton.ipyvuetify as rv
import vaex as vx

from .auth import LoginButton
from .state import State, AlertSystem
from .dataframe import NoDF
from .sidebar import sidebar
from .grid import ObjectGrid

vx.cache.on()


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
        # NOTE: deactivated
        # TODO: change to use routing to change between IPL/DR, similarly to how it's done in Zora's interface
        sl.Button(label="IPL-3", icon_name="mdi-database", text=True)
        # if State.dataset.value is not None:
        #    with lab.Menu(activator=btn, close_on_content_click=True):
        #        with sl.Column(gap="0px"):
        #            [
        #                sl.Button(
        #                    label=dataset,
        #                    on_click=create_callable(dataset),
        #                ) for dataset in State.datasets
        #                if dataset != State.dataset.value
        #            ]

        # appbar buttons
        # lab.ThemeToggle()
        sl.Button(icon_name="mdi-wheelchair-accessibility", text=True)
        LoginButton()
    # SIDEBAR
    sidebar()
    # MAIN GRID
    ObjectGrid()
    # snackbar
    AlertSystem()


@sl.component
def Layout(children):
    # route, routes = sl.use_route()

    return sl.AppLayout(sidebar_open=False, children=children, color="purple")


if __name__ == "__main__":
    Layout(Page())
