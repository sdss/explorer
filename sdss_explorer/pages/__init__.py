"""Main page component. Contains cache settings, AlertSystem instance, and general layout."""

import solara as sl
import vaex as vx

# vaex setup
if sl.server.settings.main.mode == 'production':
    vx.logging.remove_handler(
    )  # force remove handler prior to any imports on production
vx.cache.on()  # activate caching

from .dataclass import State, AlertSystem  # noqa: E402
from .components.sidebar import Sidebar  # noqa: E402
from .components.sidebar.glossary import HelpBlurb  # noqa: E402
from .components.views import ObjectGrid  # noqa: E402
from .components.views.dataframe import NoDF  # noqa: E402


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
