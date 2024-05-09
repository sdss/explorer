"""Main page component. Contains cache settings, AlertSystem instance, and general layout."""

import solara as sl
import reacton.ipyvuetify as rv
import vaex as vx

from .state import State, AlertSystem
from .sidebar import sidebar
from .grid import ObjectGrid

# NOTE: cache with these settings are in memory
# we can change this in future to a disk cache, which will be shared among worker processes, see https://vaex.io/docs/guides/caching.html
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
