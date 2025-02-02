from bokeh.models.tools import BoxZoomTool, PanTool, ResetTool
from figurebokeh import FigureBokeh

import os
from typing import Callable, Optional, cast

import ipyvuetify as v
import ipywidgets as widgets
import numpy as np
import reacton as r
import reacton.ipyvuetify as rv
import solara as sl
import traitlets as t
import vaex as vx
import xarray
from bokeh.io import output_notebook
from bokeh.events import Reset
from bokeh.models import (
    BoxSelectTool,
    ColorBar,
    LinearColorMapper,
    HoverTool,
    CategoricalColorMapper,
    LogColorMapper,
    TapTool,
    renderers,
)
from bokeh.models import (
    CustomJS,
    LogAxis,
    LinearAxis,
    LogScale,
    LinearScale,
    DataRange1d,
    Plot,
    Grid,
    WheelZoomTool,
)
from bokeh.models.glyphs import Scatter
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu

from plot_utils import (
    add_all_tools,
    generate_axes,
    generate_color_mapper_bar,
    generate_plot,
)
from state import plotstate


@sl.component()
def Page():
    df = vx.example()[:30_000]
    z = df[plotstate.color.value].values

    # generate source objects
    source = ColumnDataSource(
        data={
            "x": df[plotstate.x.value].values,
            "y": df[plotstate.y.value].values,
            "z": z,
            "sdss_id": df["L"].values,  # temp
        })

    # generate main Plot glyph
    p, menu = generate_plot(plotstate)
    # generate axes
    xaxis, yaxis, grid_x, grid_y = generate_axes(plotstate)
    p.add_layout(xaxis, "below")
    p.add_layout(yaxis, "left")
    p.add_layout(grid_x)
    p.add_layout(grid_y)

    # generate scatter points
    mapper, cb = generate_color_mapper_bar(plotstate, z)
    glyph = Scatter(
        x="x",
        y="y",
        size=8,
        marker="circle",
        fill_color={
            "field": "z",
            "transform": mapper
        },
    )
    gr = p.add_glyph(source, glyph)
    p.add_layout(cb, "right")

    # create hovertool, bound to figure object
    TOOLTIPS = (f"""
    <div>
    {plotstate.x.value}: $snap_x
    {plotstate.y.value}: $snap_x
    {plotstate.color.value}: @z
    sdss_id: @sdss_id
    </div>\n""" + """
    <style>
    div.bk-tooltip-content > div > div:not(:first-child) {
        display:none !important;
    } 
    </style>
    """)

    tools = add_all_tools(p, tooltips=TOOLTIPS)

    # add double click to open target page
    cb = CustomJS(
        args=dict(source=source),
        code="""console.log('Tap');
        console.log(source.inspected.indices);
        window.open(`https://data.sdss.org/zora/target/${source.data.sdss_id[source.inspected.indices[0]]}`, '_blank').focus();
        """,
    )
    tap = TapTool(
        behavior="inspect",
        callback=cb,
        gesture="doubletap",
    )
    p.add_tools(tap)

    with sl.GridFixed(columns=1):
        with sl.Card(elevation=0):
            FigureBokeh(
                p,
                dependencies=[
                    plotstate.x.value,
                    plotstate.y.value,
                    plotstate.color.value,
                ],
            )
    with sl.Card(margin=0):
        with sl.Columns([1, 1]):
            sl.Select(
                label="x",
                value=plotstate.x,
                values=df.get_column_names(),
            )
            sl.Select(
                label="x",
                value=plotstate.y,
                values=df.get_column_names(),
            )
        sl.Select(
            label="color",
            value=plotstate.color,
            values=df.get_column_names(),
        )
        with rv.CardActions():
            sl.lab.ThemeToggle()


if __name__ == "__main__":
    Page()
