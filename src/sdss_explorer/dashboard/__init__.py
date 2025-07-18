"""Main page component. Contains cache settings, logger setup, intializer functions, AlertSystem instance, and general layout."""

import logging
from urllib.parse import parse_qs

from bokeh.io import output_notebook
import solara as sl
import numpy as np
import vaex as vx
from solara.lab import ThemeToggle

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
)  # noqa: E402
from ..util import settings, validate_release, validate_pipeline, setup_logging  # noqa: E402
from .components.sidebar import Sidebar  # noqa: E402
from .components.sidebar.glossary import HelpBlurb  # noqa: E402
from .components.sidebar.subset_filters import flagList  # noqa: E402
from .components.views import ObjectGrid, add_view  # noqa: E402
from .components.views.dataframe import NoDF  # noqa: E402

# logging setup
PROD = sl.server.settings.main.mode == "production"

setup_logging(
    log_path=settings.logpath,
    console_log_level=settings.loglevel,
    file_log_level="INFO" if PROD else "DEBUG",
)

logger = logging.getLogger("dashboard")


def on_start():
    """Startup function, runs on every kernel instance startup and sets (some) unique sesion parameters."""
    # set session identifiers
    State._uuid.set(sl.get_session_id())
    State._kernel_id.set(sl.get_kernel_id())
    State._subset_store.set(SubsetStore())

    # connection log
    logger.info("new session connected!")

    # TODO: get user authentication via router (?) and define permissions
    # NOTE: https://github.com/widgetti/solara/issues/774

    def on_shutdown():
        """On kernel shutdown function, helps to clear memory of dataframes."""
        if State.df.value:
            State.df.value.close()
        logger.info("disconnected, culled kernel!")

    return on_shutdown


sl.lab.on_kernel_start(on_start)


@sl.component()
def Page() -> None:
    """
    Main initialize function.

    Returns:
        Implicitly returns entire app as ValueElement.
    """
    df = State.df.value

    output_notebook(
        hide_banner=True)  # required so plots can exist; loads BokehJS

    # check query params
    # NOTE: query params are not avaliable on kernel load, so it must be an effect.
    router = sl.use_router()

    def initialize():
        """Reads query params and sets initial dataframe state. Adds subset or plot as requested from query params.

        Note:
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
                    - colorlog: whether log color, either None (not ''), 'log10', or 'log1p'
                    - bintype: aggregation type. any of mean, min, max, median.
                    - colorscale: colorscale, see bokeh colormaps for valids
                    - coords: galactic, celestial; used in skyplot
                    - projection: type of projection for skyplot (i.e. hammer, mollweide, aitoff)
        """
        # unwrap query_params
        query_params = parse_qs(router.search, keep_blank_values=True)
        query_params = {k: v[0] for k, v in query_params.items()}
        logger.debug(query_params)

        ## DATAFRAME SETUP
        # setup dataframe (non-optional step)
        release: str = query_params.pop("release", "dr19").lower()
        datatype: str = query_params.pop("datatype", "star").lower()

        # check the datapath, release, and datatype
        valid_release = validate_release(settings.datapath, release)
        if not valid_release:
            logger.error("Invalid query params on release/datatype")
            return

        if datatype not in ["star", "visit"]:
            logger.warning("Invalid datatype, defaulting to star")
            datatype = "star"  # force reassignment if bad; ensures no load failure

        # set the release and datatype
        logger.info("Loading release %s and datatype %s", release, datatype)
        State._release.set(release)
        State._datatype.set(datatype)

        # this changes State.df.value & State.columns.value
        load_success = State.load_dataset()
        if not load_success:
            logger.critical("Failed to load dataset and columns!")
            return

        # set the valid pipeline when not set properly with visit spec
        if "dataset" not in query_params.keys():
            if datatype == "visit":
                query_params.update({"dataset": "thepayne"})
            else:
                query_params.update({"dataset": "mwmlite"})

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
                k: v.split(",") if
                ((k in list_subset_keys) & (len(v) > 0)) else v
                for k, v in query_params.items()
                if k in subset_keys + list_subset_keys
            }

            # validate all subset properties
            if subset_data:
                try:
                    if subset_data.get("dataset"):
                        assert validate_pipeline(State.df.value,
                                                 subset_data.get("dataset"))
                    if subset_data.get("flags"):
                        assert all({
                            flag in list(flagList.keys())
                            for flag in subset_data.get("flags")
                        }), "flags failed"
                    if subset_data.get("mapper"):
                        assert all(
                            np.isin(
                                subset_data.get("mapper"),
                                State.mapping.value["mapper"].unique(),
                                assume_unique=True,
                            )), "mapper failed"
                    if subset_data.get("carton"):
                        assert all(
                            np.isin(
                                subset_data.get("carton"),
                                State.mapping.value["alt_name"].unique(),
                                assume_unique=True,
                            )), "carton failed"

                    expr = subset_data.get("expression")
                    if expr:
                        expr = (expr.replace(".and.", " & ").replace(
                            ".or.", " | ").replace(".eq.", "=="))
                        State.df.value.validate_expression(expr)
                        subset_data["expression"] = expr
                except Exception as e:
                    logger.debug(f"Failed query params on subset parsing: {e}")

                # set first subset dataframe and columns
                try:
                    subset_data["df"]: vx.DataFrame = (State.df.value[
                        State.df.
                        value[f"(pipeline=='{subset_data.get('dataset')}')"]].
                                                       copy().extract())
                    subset_data["columns"] = State.columns.value[
                        subset_data.get("dataset")]

                    # generate subset and update
                    subsets = {"s0": Subset(**subset_data)}
                    SubsetState.index.set(len(subsets))
                    SubsetState.subsets.set(subsets)
                except TypeError as e:
                    logger.critical(
                        f"Unexpected error! All loaders passed but columns or df is None: {e}"
                    )

            # add plot if requested; only done if subset is valid
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
                    logger.debug(f"Failed query params on plot parsing: {e}")

        return

    # read query params
    sl.use_effect(initialize, [])

    # PAGE TITLE
    sl.Title("SDSS Parameter Explorer")
    with sl.AppBar():
        # main title object
        sl.AppBarTitle(children=["Parameter Explorer"])

        # help icon
        HelpBlurb()

        # theme toggle button
        if not PROD:
            ThemeToggle()

    if df is not None:
        Sidebar()  # SIDEBAR
        ObjectGrid()  # MAIN GRID
    else:
        NoDF()
    AlertSystem()  # snackbar alerts


@sl.component()
def Layout(children):
    """main solara layout component"""
    # force remove the navigation tabs from solara app layout
    route, routes = sl.use_route()

    # use vuetify material design color grey-darken-3 ; can pick new color later
    return sl.AppLayout(sidebar_open=True, children=children, color="#424242")


# app run on module instance
if __name__ == "__main__":
    Layout(Page())
