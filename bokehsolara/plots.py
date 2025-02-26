"""Individual plot viewcards"""

from reacton.ipyvuetify import ValueElement
import numpy as np
import solara as sl
import xarray
from bokeh.models import (
    BoxSelectTool,
    HoverTool,
    Rect,
    Scatter,
    TapTool,
)
from bokeh.models.mappers import (
    LinearColorMapper, )
from bokeh.models import CustomJS
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from jupyter_bokeh import BokehModel

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

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,examine"

colormaps = [x for x in colormaps if "256" in x]

index_context = sl.create_context(0)
# https://docs.bokeh.org/en/latest/docs/user_guide/interaction/js_callbacks.html#customjs-for-topics-events

from plot_themes import LIGHTTHEME, DARKTHEME
from plot_effects import add_scatter_effects, add_heatmap_effects
from plot_actions import aggregate_data


@sl.component()
def HeatmapPlot(plotstate: PlotState) -> ValueElement:
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
        z, x_centers, y_centers, _ = aggregate_data(plotstate, dff)
        print("init z", z.shape)
        return ColumnDataSource(
            data={
                "x": np.repeat(x_centers, len(y_centers)),
                "y": np.tile(y_centers, len(x_centers)),
                "z": z.flatten(),
            })

    source = sl.use_memo(generate_cds, [])

    def create_figure():
        """Creates figure with relevant objects"""
        # obtain data
        p, menu = generate_plot()
        xlimits = calculate_range(plotstate, dff, axis="x")
        ylimits = calculate_range(plotstate, dff, axis="y")
        add_axes(plotstate, p)

        fill_color = generate_color_mapper(plotstate)
        add_colorbar(plotstate, p, fill_color)

        # generate rectangles
        glyph = Rect(
            x="x",
            y="y",
            width=(xlimits[1] - xlimits[0]) / plotstate.nbins.value,
            height=(ylimits[1] - ylimits[0]) / plotstate.nbins.value,
            line_color=None,
            fill_color=fill_color,
        )
        gr = p.add_glyph(source, glyph)

        # create hovertool, bound to figure object
        add_all_tools(p, generate_tooltips(plotstate))
        add_callbacks(plotstate, dff, p, source, set_filter=None)
        return p

    p = sl.use_memo(create_figure, dependencies=[])

    pfig = FigureBokeh(p)
    add_heatmap_effects(pfig, plotstate, dff, filter, layout)
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
                "x": dff[plotstate.x.value].values,
                "y": dff[plotstate.y.value].values,
                "z": dff[plotstate.color.value].values,
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
        fill_color = generate_color_mapper(plotstate)

        # add glyph
        glyph = Scatter(
            x="x",
            y="y",
            size=8,
            fill_color=fill_color,
        )
        p.add_glyph(source, glyph)
        add_colorbar(plotstate, p, fill_color)

        # add all tools; custom hoverinfo
        add_all_tools(p, tooltips=generate_tooltips(plotstate))
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

    add_scatter_effects(pfig, plotstate, dff, filter, layout)
    return pfig
