"""Main page component. Contains cache settings, memoized context intializers, AlertSystem instance, and general layout."""

import solara as sl
from urllib.parse import parse_qs
import vaex as vx
from solara.lab import ThemeToggle
from os import getenv

# vaex setup
# NOTE: vaex gets its cache settings from envvars, see README.md
if sl.server.settings.main.mode == 'production':
    vx.logging.remove_handler(
    )  # force remove handler prior to any imports on production
vx.cache.on()  # activate caching

from .dataclass import State, AlertSystem, Alert, SubsetState  # noqa: E402
from .components.sidebar import Sidebar  # noqa: E402
from .components.sidebar.glossary import HelpBlurb  # noqa: E402
from .components.views import ObjectGrid, add_view  # noqa: E402
from .components.views.dataframe import NoDF  # noqa: E402

# development envvar
DEV = getenv('EXPLORER_DEV', False)


@sl.component()
def Page():
    df = State.df.value

    # start app state with memoized objects
    State.initialize()

    # check query params
    router = sl.use_router()

    def initialize():
        """Run once at launch (memo), reading query parameters and instantiating app as needed."""
        """
        Expected format is:
            - plottype: scatter,histogram,heatmap,skyplot,stats
            - x: main x data, any column in given dataset
            - y: main y data, any column in given dataset
            - color: main color data, any column in given dataset
            - colorscale: colorscale
            - coords: galactic, celestial; used in skyplot
            - projection: type of projection for skyplot (i.e. hammer, mollweide, aitoff)
        """
        query_params = parse_qs(router.search, keep_blank_values=True)
        if len(query_params) > 0:
            # unwrap query_params
            query_params = {k: v[0] for k, v in query_params.items()}

            # change to bool if should be bool
            toggles = ['flipx', 'flipy', 'logx', 'logy']
            query_params = {
                k: v.lower() == 'true' if k in toggles else str(v)
                for k, v in query_params.items()
            }

            # set release/datatype and load according dataset
            # underscored variables force read-only access; no reactive binding.
            State._release.set(query_params.get('release', 'dr19'))
            State._datatype.set(query_params.get('datatype', 'star'))
            State.load_dataset(State.release, State.datatype)

            # update the first (s0) subset based on query params
            # NOTE: this may be breaking if we save user sessions to cookies/server and try to restore
            subset_keys = ['dataset', 'expression']
            list_subset_keys = ['mapper', 'carton', 'flags']

            # dict comprehension to get relevant kwargs and convert to list if necessary
            SubsetState.update_subset(
                's0', **{
                    k: v.split(',') if k in list_subset_keys else v
                    for k, v in query_params.items()
                    if k in subset_keys + list_subset_keys
                })

            # add relevant plots
            try:
                plottype = query_params.pop('plottype')
                add_view(plottype, **query_params)
            except Exception:
                pass

        return

    sl.use_memo(initialize, [])

    # PAGE TITLE
    sl.Title("SDSS Parameter Explorer")
    with sl.AppBar():
        # main title object
        sl.AppBarTitle(children=["Parameter Explorer"])

        # help icon
        HelpBlurb()

        # theme toggle button
        if DEV:
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


@sl.component()
def Layout(children):
    # force remove the navigation tabs from solara app layout
    route, routes = sl.use_route()

    # use vuetify material design color grey-darken-3 ; can pick new color later
    return sl.AppLayout(sidebar_open=True, children=children, color="#424242")


# app run
if __name__ == "__main__":
    Layout(Page())
