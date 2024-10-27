"""Main page component. Contains cache settings, memoized context intializers, AlertSystem instance, and general layout."""

import solara as sl
from solara.hooks.misc import use_unique_key
import vaex as vx
from solara.lab import ThemeToggle
from os import getenv

# vaex setup
# NOTE: vaex gets its cache settings from envvars, see README.md
if sl.server.settings.main.mode == 'production':
    vx.logging.remove_handler(
    )  # force remove handler prior to any imports on production
vx.cache.on()  # activate caching

from .dataclass import State, AlertSystem  # noqa: E402
from .dataclass.state import SubsetStore  # noqa: E402
from .components.sidebar import Sidebar  # noqa: E402
from .components.sidebar.glossary import HelpBlurb  # noqa: E402
from .components.views import ObjectGrid  # noqa: E402
from .components.views.dataframe import NoDF  # noqa: E402

# development envvar
DEV = getenv('EXPLORER_DEV', False)


@sl.component()
def Page():
    df = State.df.value

    # start app state with memoized objects?
    State.initialize()

    # PAGE TITLE
    # TODO: Will this properly
    # TODO: update the title with release from query parameter
    sl.Title("SDSS Parameter Explorer")
    with sl.AppBar():
        # main title object
        sl.AppBarTitle(children=["Parameter Explorer"])

        # help icon
        HelpBlurb()

        # theme toggle button
        if DEV:
            ThemeToggle()

    print(type(df))
    if df is not None:
        # SIDEBAR
        Sidebar()
        # MAIN GRID
        ObjectGrid()
    else:
        NoDF()
    # snackbar
    AlertSystem()


@sl.component()
def Layout(children):
    # force remove the navigation tabs from solara app layout
    route, routes = sl.use_route()

    # use vuetify material design color grey-darken-3 ; can pick new color later
    return sl.AppLayout(sidebar_open=True, children=children, color="#424242")


# app run
if __name__ == "__main__":
    Layout(Page())
