"""Main page component. Contains cache settings, memoized context intializers, AlertSystem instance, and general layout."""

import solara as sl
import numpy as np
from urllib.parse import parse_qs
import vaex as vx
from solara.lab import ThemeToggle
from os import getenv
import os

# vaex setup
# NOTE: vaex gets its cache settings from envvars, see README.md
if sl.server.settings.main.mode == "production":
    vx.logging.remove_handler(
    )  # force remove handler prior to any imports on production
vx.cache.on()  # activate caching

from .dataclass import (
    State,
    Subset,
    SubsetStore,
    AlertSystem,
    Alert,
    SubsetState,
    _datapath,
)  # noqa: E402
from .util import validate_release, validate_pipeline
from .components.sidebar import Sidebar  # noqa: E402
from .components.sidebar.glossary import HelpBlurb  # noqa: E402
from .components.sidebar.subset_filters import flagList  # noqa: E402
from .components.views import ObjectGrid, add_view  # noqa: E402
from .components.views.dataframe import NoDF  # noqa: E402

# development envvar
DEV = getenv("EXPLORER_DEV", False)


@sl.lab.on_kernel_start
def on_start():
    # set session identifiers
    State._uuid.set(sl.get_session_id())
    State._kernel_id.set(sl.get_kernel_id())
    State._subset_store.set(SubsetStore())

    # TODO: get user authentication via router (?) and define permissions
    # NOTE: https://github.com/widgetti/solara/issues/774

    def on_shutdown():
        """On kernel shutdown function, helps to clear memory."""
        State.df.value.close()

    return on_shutdown


@sl.component()
def Page():
    df = State.df.value

    # check query params
    router = sl.use_router()

    def initialize():
        """Run once at launch after first render, reading query parameters and instantiating app as needed."""
        """
        Expected format is:
            app properties:
                - release: data release, set by zora
                - datatype: star or visit
            subset properties:
                - dataset: the dataset to load
                - expression: an expression, use .and. in place of '&'
                - mapper: the mappers to init the subset with
                - carton: the cartons to init the subset with
                - flags: the flags to init the subset with
            first plot properties:
                - plottype: scatter,histogram,heatmap,skyplot,stats
                - x: main x data, any column in given dataset
                - y: main y data, any column in given dataset
                - color: main color data, any column in given dataset
                - colorscale: colorscale
                - coords: galactic, celestial; used in skyplot
                - projection: type of projection for skyplot (i.e. hammer, mollweide, aitoff)
        """
        # unwrap query_params
        query_params = parse_qs(router.search, keep_blank_values=True)
        query_params = {k: v[0] for k, v in query_params.items()}

        # setup dataframe (non-optional step)
        release: str = query_params.pop("release", "dr19")
        datatype: str = query_params.pop("datatype", "star")
        try:
            assert validate_release(_datapath(), release), "release invalid"
            assert (datatype == "star") or (datatype
                                            == "visit"), "datatype invalid"

            # set the release and datatype
            State._release.set(release)
            State._datatype.set(datatype)
            State.load_dataset()  # this changes State.df.value
        except Exception as e:
            # TODO: logging
            print("invalid query params on release/datatype:", e)
            return

        # set valid pipeline when not set properly with visit spec
        if (datatype == "visit") & ("dataset" not in query_params.keys()):
            query_params.update({"dataset": "apogeenet"})

        # parse subset/plot initializes
        if len(query_params) > 0:
            # change plot params to bool if should be bool
            toggles = ["flipx", "flipy", "logx", "logy"]
            query_params = {
                k: v.lower() == "true" if k in toggles else str(v).lower()
                for k, v in query_params.items()
            }

            # update the first (s0) subset based on query params
            # dict comprehension to get relevant kwargs and convert to list if necessary
            # NOTE: this may be breaking if we save user sessions to cookies/server and try to restore before this operation
            subset_keys = ["dataset", "expression"]
            list_subset_keys = ["mapper", "carton", "flags"]
            subset_data = {
                k: v.split(",") if k in list_subset_keys else v
                for k, v in query_params.items()
                if k in subset_keys + list_subset_keys
            }

            # validate all subset properties
            try:
                assert validate_pipeline(State.df.value,
                                         subset_data.get("dataset"))
                # assert all({
                #    flag in flagList.keys()
                #    for flag in subset_data.get("flags")
                # }), "flags failed"
                # assert all(
                #    np.isin(
                #        subset_data.get("mapper"),
                #        State.mapping.value["mapper"].unique(),
                #        assume_unique=True,
                #    )), "mapper failed"
                # assert all(
                #    np.isin(
                #        subset_data.get("carton"),
                #        State.mapping.value["alt_name"].unique(),
                #        assume_unique=True,
                #    )), "carton failed"

                expr = subset_data.get("expression")
                if expr:
                    State.df.value.validate_expression(expr)
            except Exception as e:
                print(e)
                return

            # generate subset and update
            subsets = {"s0": Subset(**subset_data)}
            SubsetState.index.set(len(subsets))
            SubsetState.subsets.set(subsets)

            # add plot if requested
            if "plottype" in query_params.keys():
                try:
                    columns = State.df.value.get_column_names()
                    for coltype in ["x", "y", "color"]:
                        col = query_params.get(coltype, None)
                        if col:
                            # TODO: update to ensure in the specific dataset
                            assert col in columns
                    plottype = query_params.pop("plottype")
                    add_view(plottype, **query_params)
                except Exception as e:
                    # TODO: do we want logging/alerts here logging here
                    print("query params error:", e)
                    return

        return

    # create unique user app state
    sl.use_effect(initialize, [])

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
        Sidebar()  # SIDEBAR
        ObjectGrid()  # MAIN GRID
    else:
        NoDF()
    AlertSystem()  # snackbar alerts


@sl.component()
def Layout(children):
    # force remove the navigation tabs from solara app layout
    route, routes = sl.use_route()

    # use vuetify material design color grey-darken-3 ; can pick new color later
    return sl.AppLayout(sidebar_open=True, children=children, color="#424242")


# app run on module instance
if __name__ == "__main__":
    Layout(Page())
