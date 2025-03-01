"""Individual plot viewcards"""

import asyncio
from reacton.ipyvuetify import ValueElement
from functools import reduce
import operator
import numpy as np
import solara as sl
from bokeh.models import (
    BooleanFilter,
    CDSView,
    HoverTool,
    Quad,
    Rect,
    Scatter,
)
from bokeh.palettes import __palettes__ as colormaps
from bokeh.plotting import ColumnDataSource

from plot_utils import (
    add_all_tools,
    add_callbacks,
    calculate_range,
    generate_color_mapper,
    generate_tooltips,
    add_axes,
    add_colorbar,
    generate_plot,
)
from state import PlotState, df, GridState
from figurebokeh import FigureBokeh
from plot_themes import LIGHTTHEME, DARKTHEME
from plot_effects import (
    add_histogram_effects,
    add_scatter_effects,
    add_heatmap_effects,
    add_common_effects,
)
from plot_actions import (
    reset_range,
    aggregate_data,
    fetch_data,
    update_tooltips,
)

colormaps = [x for x in colormaps if "256" in x]

index_context = sl.create_context(0)


@sl.component()
def HistogramPlot(plotstate: PlotState) -> ValueElement:
    """Histogram plot"""
    filter, set_filter = sl.use_cross_filter(id(df), name="scatter")
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # TODO: fix to make its own reactive var (computed) thing
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
            # Alert.update('Failed to initialize! {e}. Using dummy data.')
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
        gr = p.add_glyph(source, glyph)
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
    add_common_effects(pfig, plotstate, dff, layout)
    return pfig


@sl.component()
def HeatmapPlot(plotstate: PlotState) -> ValueElement:
    """2D Histogram (heatmap) plot"""
    filter, set_filter = sl.use_cross_filter(id(df), name="scatter")
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # TODO: fix to make its own reactive var (computed) thing
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
            color, x_centers, y_centers, _ = aggregate_data(plotstate, dff)
        except Exception:
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
        glyph = Rect(
            x="x",
            y="y",
            width=(xlimits[1] - xlimits[0]) / plotstate.nbins.value,
            height=(ylimits[1] - ylimits[0]) / plotstate.nbins.value,
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
    add_common_effects(pfig, plotstate, dff, layout)
    return pfig


@sl.component
def ScatterPlot(plotstate: PlotState) -> ValueElement:
    filter, set_filter = sl.use_cross_filter(id(df), name="scatter")
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
        print("updating local filter")
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
            print("first", e)
            pass
        try:
            lims = np.array(ranges[1])
            assert not np.all(lims == np.nan)
            ymax = np.nanmax(lims)
            ymin = np.nanmin(lims)
            yfilter = df[
                f"(({plotstate.y.value} > {ymin}) & ({plotstate.y.value} < {ymax}))"]

        except Exception as e:
            print("second", e)
            pass
        if xfilter is not None and yfilter is not None:
            filters = [xfilter, yfilter]
        else:
            filters = [xfilter if xfilter is not None else yfilter]
        combined = reduce(operator.and_, filters[1:], filters[0])
        print("combined", combined)
        return combined

    # if start changes end changes too (likely)
    local_filter = sl.use_memo(update_filter,
                               dependencies=[ranges[0], ranges[1]])

    async def debounced_filter():
        print("filtering debounce")
        await asyncio.sleep(0.05)
        return local_filter

    debounced_local_filter = sl.lab.use_task(debounced_filter,
                                             dependencies=[local_filter],
                                             prefer_threaded=False)

    def get_dff():
        filters = []
        if debounced_local_filter.finished:
            if debounced_local_filter.value == local_filter:
                if debounced_local_filter.value is not None:
                    filters.append(debounced_local_filter.value)
                    print("added debounce local")
        if filter is not None:
            filters.append(filter)
            print("added cross")
        if filters:
            total_filter = reduce(operator.and_, filters[1:], filters[0])
            print("returning filtered")
            dfe = df[total_filter]
        else:
            print("returning normal")
            dfe = df
        try:
            if len(dfe) > 10001:  # bugfix
                print("returing sliced")
                return dfe[:10_000]
            else:
                print("returing as is")
                return dfe
        except Exception:
            return dfe

    dff = sl.use_memo(
        get_dff, dependencies=[df, filter, debounced_local_filter.finished])

    def generate_cds():
        try:
            assert len(dff) > 0, "zero data in subset!"
            x = fetch_data(plotstate, dff, "x").values
            y = fetch_data(plotstate, dff, "y").values
            color = fetch_data(plotstate, dff, "color").values
            sdss_id = dff["sdss_id"].values
        except Exception as e:
            print("scatter init", e)
            # Alert.update('Failed to initialize plot! {e} Using dummy data')
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
            print("range update ocurring")
            print(event)
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

    dfe = sl.use_memo(_get_dfe, dependencies=[filter])

    # workaround to make reset button aware of dff bounds
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
    add_common_effects(pfig, plotstate, dff, layout)
    return pfig
