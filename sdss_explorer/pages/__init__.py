"""Main page component. Contains cache settings, AlertSystem instance, and general layout."""

import solara as sl
import vaex as vx

from .state import State, AlertSystem
from .dataframe import NoDF
from .sidebar import sidebar
from .grid import ObjectGrid
from .glossary import HelpBlurb

# NOTE: cache with these settings are in memory
# we can change this in future to a disk cache, which will be shared among worker processes, see https://vaex.io/docs/guides/caching.html
vx.cache.on()


@sl.component
def Page():
    df = State.df.value

    # PAGE TITLE
    # TODO: make this adaptive in some cool way
    sl.Title("SDSS Parameter Explorer")
    with sl.AppBar():
        # TODO - post collab meeting
        # TODO - add query parameter option for the data release
        # TODO - update the title with release from query parameter
        # main title object
        sl.AppBarTitle(children=["IPL-3 Parameter Explorer"])

        # help icon
        HelpBlurb()

    if df is not None:
        # SIDEBAR
        sidebar()
        # MAIN GRID
        ObjectGrid()
    else:
        NoDF()
    # snackbar
    AlertSystem()


@sl.component
def Layout(children):
    # force remove the navigation tabs from solara app layout
    route, routes = sl.use_route()

    # use vuetify material design color grey-darken-3 ; can pick new color later
    return sl.AppLayout(sidebar_open=True, children=children, color="#424242")


if __name__ == "__main__":
    Layout(Page())
