"""Main page component. Contains cache settings, AlertSystem instance, and general layout."""

import solara as sl
import vaex as vx
from solara.lab import ThemeToggle

from .dataclass import State, AlertSystem
from .components.sidebar import Sidebar
from .components.sidebar.glossary import HelpBlurb
from .components.views import ObjectGrid
from .components.views.dataframe import NoDF

# NOTE: cache with these settings are in memory
# we can change this in future to a disk cache, which will be shared among worker processes, see https://vaex.io/docs/guides/caching.html
vx.cache.on()

# disable the vaex built-in logging (clogs on FileNotFounds et al)
# TODO: set to only remove on production mode (no reload context; is this registered as a variable i can access?)
# alternatively can I pass it up to valis?
vx.logging.remove_handler()


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
        ThemeToggle()

    if df is not None:
        # SIDEBAR
        Sidebar()
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
