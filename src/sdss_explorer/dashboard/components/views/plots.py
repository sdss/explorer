"""Individual plot components"""

import asyncio
import operator
import logging
from functools import reduce

import numpy as np
import solara as sl
import pandas as pd
import vaex as vx
import reacton.ipyvuetify as rv
from reacton.ipyvuetify import ValueElement
from bokeh.models import (
    HoverTool,
    Quad,
    Rect,
    Scatter,
)
from bokeh.plotting import ColumnDataSource

from .dataframe import ModdedDataTable, TargetsDataTable
from .plot_settings import show_settings
from .plot_utils import (
    add_all_tools,
    add_callbacks,
    check_categorical,
    calculate_range,
    generate_color_mapper,
    generate_tooltips,
    add_axes,
    add_colorbar,
    generate_plot,
)
from .figurebokeh import FigureBokeh
from .plot_themes import LIGHTTHEME, DARKTHEME
from .plot_effects import (
    add_histogram_effects,
    add_scatter_effects,
    add_heatmap_effects,
    add_common_effects,
)
from .plot_actions import (
    reset_range,
    aggregate_data,
    fetch_data,
    update_mapping,
    update_tooltips,
)

from ...dataclass import PlotState, SubsetState, GridState, use_subset, Alert, VCData

logger = logging.getLogger("dashboard")

# index context for grid
# NOTE: must be initialized here to avoid circular imports
index_context = sl.create_context(0)
"""context: used for tracing parent card in the grid for height resizing"""


@sl.component()
def show_plot(plottype, del_func, **kwargs):
    """Helper function to show a specific plot type with its settings. Wraps all into card.

    Note:
        `PlotState` is instantiated here.

    Args:
        plottype (str): plot type
        del_func (Callable): callable to delete this plot from the grid.
        kwargs (kwargs): overload for plot variable setup

    """
    # NOTE: force set to grey darken-3 colour for visibility of card against grey darken-4 background
    dark = sl.lab.use_dark_effective()
    with rv.Card(
            class_="grey darken-3" if dark else "grey lighten-3",
            style_="width: 100%; height: 100%",
    ) as main:
        # NOTE: current key has to be memoized outside the instantiation (why I couldn't tell you)
        current_key = sl.use_memo(
            lambda: list(SubsetState.subsets.value.keys())[-1],
            dependencies=[])
        plotstate = PlotState(plottype, current_key, **kwargs)
        df = SubsetState.subsets.value[current_key].df

        def add_to_grid():
            """Adds a pointer/reference to PlotState instance in GridState for I/O."""
            GridState.states.set(list(GridState.states.value + [plotstate]))
            return None

        sl.use_memo(add_to_grid, dependencies=[])  # runs once

        if df is not None:
            with rv.CardText():
                with sl.Column(classes=[
                        "grey darken-3" if dark else "grey lighten-3"
                ]):
                    if plottype == "histogram":
                        HistogramPlot(plotstate)
                    elif plottype == "heatmap":
                        HeatmapPlot(plotstate)
                    elif plottype == "scatter":
                        ScatterPlot(plotstate)
                    elif plottype == "stats":
                        StatisticsTable(plotstate)
                    elif plottype == "targets":
                        TargetsTable(plotstate)
                    btn = sl.Button(
                        icon_name="mdi-settings",
                        outlined=False,
                        classes=[
                            "grey darken-3" if dark else "grey lighten-3"
                        ],
                    )
                    with sl.lab.Menu(activator=btn,
                                     close_on_content_click=False):
                        with sl.Card(margin=0):
                            show_settings(plottype, plotstate)
                            sl.Button(
                                icon_name="mdi-delete",
                                color="red",
                                block=True,
                                on_click=del_func,
                            )
    return main


@sl.component()
def HistogramPlot(plotstate: PlotState) -> ValueElement:
    """Histogram plot component.

    Reactives:
        df: subset dataframe
        filter: subset filter hook
        layout: layout, used to hook height resizing
        dff: filtered dataframe

    Args:
        plotstate: plot variables
    """
    df: vx.DataFrame = SubsetState.subsets.value[plotstate.subset.value].df
    filter, set_filter = use_subset(id(df), plotstate.subset, name="histogram")
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.lab.use_task(update_grid, dependencies=[GridState.grid_layout.value])
    if filter is not None:
        dff = df[filter]
    else:
        dff = df

    def generate_cds():
        try:
            centers, edges, counts = aggregate_data(plotstate, dff)
        except Exception as e:
            Alert.update(f"Failed to initialize! {e}. Using dummy data.")
            centers = [0, 1, 2]
            edges = [0, 1, 2, 3]
            counts = [0, 0, 0]
        return ColumnDataSource(
            data={
                "centers": centers,
                "left": edges[:-1],
                "right": edges[1:],
                "y": counts,
            })

    source = sl.use_memo(generate_cds, dependencies=[])

    def create_figure():
        """Creates figure with relevant objects"""
        # obtain data
        p, menu = generate_plot()
        add_axes(plotstate, p)

        # generate rectangles
        glyph = Quad(
            top="y",
            bottom=0,
            left="left",
            right="right",
            fill_color="skyblue",
        )
        p.add_glyph(source, glyph)
        # p.y_range.bounds = [0, None] NOTE: tried this but it makes it janky to zoom

        p.y_range.start = 0  # force set 0 at start

        # create hovertool, bound to figure object
        add_all_tools(p, generate_tooltips(plotstate))
        for tool in p.toolbar.tools:
            if isinstance(tool, HoverTool):
                tool.point_policy = "follow_mouse"
        update_tooltips(plotstate, p)
        add_callbacks(plotstate, dff, p, source, set_filter=set_filter)
        return p

    p = sl.use_memo(create_figure, dependencies=[])

    # workaround to have the reset ranges be the ranges of dff
    def add_reset_callback():
        # WARNING: temp method until Bokeh adds method for remove_on_event
        def on_reset(attr, old, new):
            """Range resets"""

            with p.hold(render=True):
                reset_range(plotstate, p, dff, axis="x")
                reset_range(plotstate, p, dff, axis="y")

        p.on_change("name", on_reset)

        # dump on regeneration
        def cleanup():
            p.remove_on_change("name", on_reset)

        return cleanup

    sl.use_effect(add_reset_callback, dependencies=[dff])

    pfig = FigureBokeh(p, dark_theme=DARKTHEME, light_theme=LIGHTTHEME)
    add_histogram_effects(pfig, plotstate, dff, filter)
    add_common_effects(pfig, source, plotstate, dff, set_filter, layout)
    return pfig


@sl.component()
def HeatmapPlot(plotstate: PlotState) -> ValueElement:
    """2D Histogram (heatmap) plot

    Reactives:
        df: subset dataframe
        filter: subset filter hook
        layout: layout, used to hook height resizing
        dff: filtered dataframe

    Args:
        plotstate: plot variables
    """
    df: vx.DataFrame = SubsetState.subsets.value[plotstate.subset.value].df
    filter, set_filter = use_subset(id(df), plotstate.subset, name="heatmap")
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.lab.use_task(update_grid, dependencies=[GridState.grid_layout.value])
    if filter is not None:
        dff = df[filter]
    else:
        dff = df

    def generate_cds():
        for axis in {"x", "y", "color"}:
            col = getattr(plotstate, axis).value
            if check_categorical(col):
                update_mapping(plotstate, axis="x")
        try:
            color, x_centers, y_centers, _ = aggregate_data(plotstate, dff)
        except Exception as e:
            logger.debug("failed plot init" + str(e))
            Alert.update("Failed to initialize heatmap" + str(e))
            x_centers = [0, 1, 2, 3]
            y_centers = [0, 1, 2, 3]
            color = np.zeros((4, 4))
        return ColumnDataSource(
            data={
                "x": np.repeat(x_centers, len(y_centers)),
                "y": np.tile(y_centers, len(x_centers)),
                "color": color.flatten(),
            })

    source = sl.use_memo(generate_cds, [])

    def create_figure():
        """Creates figure with relevant objects"""
        # obtain data
        p, menu = generate_plot(range_padding=0.0)
        xlimits = calculate_range(plotstate, dff, axis="x")
        ylimits = calculate_range(plotstate, dff, axis="y")

        # add grid, but disable its lines
        add_axes(plotstate, p)
        p.center[0].grid_line_color = None
        p.center[1].grid_line_color = None

        mapper = generate_color_mapper(plotstate, color=source.data["color"])
        # generate rectangles
        logger.debug(source.data)
        logger.debug(f"{mapper.low} to {mapper.high}")
        glyph = Rect(
            x="x",
            y="y",
            width=abs(xlimits[1] - xlimits[0]) / plotstate.nbins.value,
            height=abs(ylimits[1] - ylimits[0]) / plotstate.nbins.value,
            dilate=True,
            line_color=None,
            fill_color={
                "field": "color",
                "transform": mapper
            },
        )
        add_colorbar(plotstate, p, mapper, source.data["color"])
        gr = p.add_glyph(source, glyph)

        # create hovertool, bound to figure object
        add_all_tools(p, generate_tooltips(plotstate))
        update_tooltips(plotstate, p)
        add_callbacks(plotstate, dff, p, source, set_filter=set_filter)
        return p

    p = sl.use_memo(create_figure, dependencies=[])

    # workaround to have the reset ranges be the ranges of dff
    def add_reset_callback():
        # WARNING: temp method until Bokeh adds method for remove_on_event
        def on_reset(attr, old, new):
            """Range resets"""

            with p.hold(render=True):
                reset_range(plotstate, p, dff, axis="x")
                reset_range(plotstate, p, dff, axis="y")

        p.on_change("name", on_reset)

        # dump on regeneration
        def cleanup():
            p.remove_on_change("name", on_reset)

        return cleanup

    sl.use_effect(add_reset_callback, dependencies=[dff])

    pfig = FigureBokeh(p, dark_theme=DARKTHEME, light_theme=LIGHTTHEME)
    add_heatmap_effects(pfig, plotstate, dff, filter)
    add_common_effects(pfig, source, plotstate, dff, set_filter, layout)
    return pfig


@sl.component()
def ScatterPlot(plotstate: PlotState) -> ValueElement:
    """ScatterPlot component. Adaptively rerenders based on zoom state.

    Reactives:
        df: subset dataframe
        filter: subset filter hook
        layout: layout, used to hook height resizing
        ranges: current plot ranges, used for adaptive rerendering
        dff: filtered dataframe
        dfe: filtered dataframe _without_ local filter, used for resetting ranges

    Args:
        plotstate: plot variables
    """

    df: vx.DataFrame = SubsetState.subsets.value[plotstate.subset.value].df
    filter, set_filter = use_subset(id(df), plotstate.subset, name="scatter")
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})
    ranges, set_ranges = sl.use_state([[np.nan, np.nan], [np.nan, np.nan]])

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.lab.use_task(update_grid, dependencies=[GridState.grid_layout.value])

    def update_filter():
        logger.debug("updating local filter")
        xfilter = None
        yfilter = None

        try:
            lims = np.array(ranges[0])
            assert not np.all(lims == np.nan)
            xmax = np.nanmax(lims)
            xmin = np.nanmin(lims)
            xfilter = df[
                f"(({plotstate.x.value} > {xmin}) & ({plotstate.x.value} < {xmax}))"]
        except Exception as e:
            pass
        try:
            lims = np.array(ranges[1])
            assert not np.all(lims == np.nan)
            ymax = np.nanmax(lims)
            ymin = np.nanmin(lims)
            yfilter = df[
                f"(({plotstate.y.value} > {ymin}) & ({plotstate.y.value} < {ymax}))"]

        except Exception as e:
            pass
        if xfilter is not None and yfilter is not None:
            filters = [xfilter, yfilter]
        else:
            filters = [xfilter if xfilter is not None else yfilter]
        combined = reduce(operator.and_, filters[1:], filters[0])
        logger.debug("combined = " + str(combined))
        return combined

    # update on dataset (df) change, or range update
    local_filter = sl.use_memo(update_filter,
                               dependencies=[df, ranges[0], ranges[1]])

    async def debounced_filter():
        await asyncio.sleep(0.05)
        return local_filter

    # debounced output
    debounced_local_filter = sl.lab.use_task(debounced_filter,
                                             dependencies=[local_filter],
                                             prefer_threaded=False)

    # combine the filters every render
    filters = []
    try:
        if debounced_local_filter.finished:
            if debounced_local_filter.value == local_filter:
                if debounced_local_filter.value is not None:
                    filters.append(debounced_local_filter.value)
        if filter is not None:
            filters.append(filter)
        if filters:
            total_filter = reduce(operator.and_, filters[1:], filters[0])
            dff = df[total_filter]
        else:
            dff = df
    except Exception:
        dff = df
    if dff is not None:
        if len(dff) > 10001:  # bugfix
            dff = dff[:10_000]

    def generate_cds():
        """Generate initial CDS object. Runs once"""
        logger.debug("generating cds")
        try:
            assert len(dff) > 0, "zero data in subset!"
            x = fetch_data(plotstate, dff, "x").values
            y = fetch_data(plotstate, dff, "y").values
            color = fetch_data(plotstate, dff, "color").values
            sdss_id = dff["sdss_id"].values
        except Exception as e:
            logger.debug("failed scatter init" + str(e))
            Alert.update(f"Failed to initialize plot! {e} Using dummy data")
            x = [1, 2, 3, 4]
            y = [1, 2, 3, 4]
            color = [1, 2, 3, 4]
            sdss_id = [1, 2, 3, 4]
        source = ColumnDataSource(data={
            "x": x,
            "y": y,
            "color": color,
            "sdss_id": sdss_id,
        })
        logger.debug("cds = " + str(source.data))
        return source

    source = sl.use_memo(
        generate_cds,
        dependencies=[],
    )

    def create_figure():
        """Creates figure with relevant objects"""
        p, menu = generate_plot()
        # generate and add axes
        add_axes(plotstate, p)

        # generate scatter points and colorbar
        mapper = generate_color_mapper(plotstate, dff=dff)

        # add glyph
        glyph = Scatter(x="x",
                        y="y",
                        size=8,
                        fill_color={
                            "field": "color",
                            "transform": mapper
                        })
        p.add_glyph(source, glyph)
        add_colorbar(plotstate, p, mapper, source.data["color"])

        # add all tools; custom hoverinfo
        add_all_tools(p)
        update_tooltips(plotstate, p)
        add_callbacks(plotstate, dff, p, source, set_filter=set_filter)

        # add our special range callback for adaptive rerenders
        def on_range_update(event):
            logger.debug("range update ocurring")
            set_ranges([[event.x0, event.x1], [event.y0, event.y1]])

        from bokeh.events import RangesUpdate

        p.on_event(RangesUpdate, on_range_update)

        return p

    p = sl.use_memo(
        create_figure,
        dependencies=[],
    )

    # externally filtered df onlu
    # NOTE: this is different from dff, which is the fully filtered one
    def _get_dfe():
        if filter is not None:
            return df[filter]
        return df

    dfe = sl.use_memo(_get_dfe, dependencies=[df, filter])

    # workaround to make reset button aware of dff bounds are given the filtering
    # NOTE:reset callback must be aware of what dfe is and dump as necessary
    def add_reset_callback():
        # WARNING: temp method until Bokeh adds method for remove_on_event
        def on_reset(attr, old, new):
            """Range resets"""

            with p.hold(render=True):
                reset_range(plotstate, p, dfe, axis="x")
                reset_range(plotstate, p, dfe, axis="y")
                set_ranges([[np.nan, np.nan], [np.nan, np.nan]])

        p.on_change("name", on_reset)

        # dump on regeneration
        def cleanup():
            p.remove_on_change("name", on_reset)

        return cleanup

    sl.use_effect(add_reset_callback, dependencies=[dfe])

    pfig = FigureBokeh(
        p,
        dependencies=[],
        dark_theme=DARKTHEME,
        light_theme=LIGHTTHEME,
    )

    add_scatter_effects(pfig, plotstate, dff, filter)
    add_common_effects(pfig, source, plotstate, dff, set_filter, layout)
    return pfig


@sl.component()
def StatisticsTable(state):
    """Statistics description view for the dataset."""
    df: vx.DataFrame = SubsetState.subsets.value[state.subset.value].df
    filter, set_filter = use_subset(id(df), state.subset, name="statsview")
    columns, set_columns = state.columns.value, state.columns.set

    # the summary table is its own DF (for render purposes)
    def generate_describe() -> pd.DataFrame:
        """Generates the description table only on column/filter updates"""
        # INFO: vaex returns a pandas df.describe()
        if filter:
            dff = df[filter].extract()  # only need df here, so make here
        else:
            dff = df

        try:
            assert len(dff) > 0
            dfd = dff[columns].describe(strings=False)
        except Exception as e:
            Alert.update(
                "Failed to get statistics! Is your data too small for aggregations?",
                color="warning",
            )
            logger.error(f"Failure on StatsTable: {e}")
            dfd = pd.DataFrame({"error": ["no"], "encountered": ["data"]})
        return dfd

    result = sl.lab.use_task(generate_describe,
                             dependencies=[filter, columns,
                                           len(columns)])

    def remove_column(name):
        """Removes column from column list"""
        # perform removal via slice (cannot modify inplace)
        # TODO: check if slicing is actually necessary

        q = None
        for i, col in enumerate(columns):
            if col == name:
                q = i
                break

        set_columns(columns[:q] + columns[q + 1:])

    column_actions = [
        # TODO: a more complex action in here?
        sl.ColumnAction(icon="mdi-delete",
                        name="Remove column",
                        on_click=remove_column),
    ]

    sl.ProgressLinear(result.pending)
    if ~result.not_called and result.latest is not None:
        ModdedDataTable(
            result.latest,
            items_per_page=7,
            column_actions=column_actions,
        )
    else:
        sl.Info("Loading...")
    return


@sl.component()
def TargetsTable(plotstate):
    """Shows the table view, loading lazily via solara components."""
    subset = plotstate.subset.value
    df = SubsetState.subsets.value[subset].df
    filter, _ = use_subset(id(df), plotstate.subset, name="filter-tableview")

    if filter is not None:
        dff = df[filter]
    else:
        dff = df

    dff = dff[plotstate.columns.value]

    return TargetsDataTable(
        dff,
        plotstate.columns.value,
        items_per_page=10,
    )
