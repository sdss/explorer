"""Individual plot viewcards"""

from reacton.ipyvuetify import ValueElement
import numpy as np
import solara as sl
from bokeh.models import (
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
from plot_effects import add_scatter_effects, add_heatmap_effects, add_common_effects
from plot_actions import aggregate_data, fetch_data, update_tooltips

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
        edges, counts = aggregate_data(plotstate, dff)
        return ColumnDataSource(data={
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
        p.y_range.bounds = [0, None]

        # create hovertool, bound to figure object
        add_all_tools(p, generate_tooltips(plotstate))
        update_tooltips(plotstate, p)
        add_callbacks(plotstate, dff, p, source, set_filter=None)
        return p

    p = sl.use_memo(create_figure, dependencies=[])

    pfig = FigureBokeh(p, dark_theme=DARKTHEME, light_theme=LIGHTTHEME)
    # add_heatmap_effects(pfig, plotstate, dff, filter)
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
        color, x_centers, y_centers, _ = aggregate_data(plotstate, dff)
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
        p, menu = generate_plot()
        xlimits = calculate_range(plotstate, dff, axis="x")
        ylimits = calculate_range(plotstate, dff, axis="y")

        # add grid, but disable its lines
        add_axes(plotstate, p)
        p.center[0].grid_line_color = None
        p.center[1].grid_line_color = None

        mapper = generate_color_mapper(plotstate, z=source.data["color"])
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

        # force reset ranges, we want no pad
        p.x_range.start = xlimits[0]
        p.x_range.end = xlimits[1]
        p.y_range.start = ylimits[0]
        p.y_range.end = ylimits[1]

        # create hovertool, bound to figure object
        add_all_tools(p, generate_tooltips(plotstate))
        update_tooltips(plotstate, p)
        add_callbacks(plotstate, dff, p, source, set_filter=None)
        return p

    p = sl.use_memo(create_figure, dependencies=[])

    pfig = FigureBokeh(p, dark_theme=DARKTHEME, light_theme=LIGHTTHEME)
    add_heatmap_effects(pfig, plotstate, dff, filter)
    add_common_effects(pfig, plotstate, dff, layout)
    return pfig


@sl.component
def ScatterPlot(plotstate: PlotState) -> ValueElement:
    filter, set_filter = sl.use_cross_filter(id(df), name="scatter")
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

    source = sl.use_memo(
        lambda: ColumnDataSource(
            data={
                "x": fetch_data(plotstate, dff, "x").values,
                "y": fetch_data(plotstate, dff, "y").values,
                "color": fetch_data(plotstate, dff, "color").values,
                "sdss_id": dff["L"].values,  # temp
            }),
        dependencies=[],
    )

    def create_figure():
        """Creates figure with relevant objects"""
        p, menu = generate_plot()
        # generate and add axes
        add_axes(plotstate, p)

        # generate scatter points and colorbar
        mapper = generate_color_mapper(plotstate)

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
        add_callbacks(plotstate, dff, p, source)

        return p

    p = sl.use_memo(
        create_figure,
        dependencies=[],
    )

    pfig = FigureBokeh(
        p,
        dependencies=[],
        dark_theme=DARKTHEME,
        light_theme=LIGHTTHEME,
    )

    add_scatter_effects(pfig, plotstate, dff, filter)
    add_common_effects(pfig, plotstate, dff, layout)
    return pfig
