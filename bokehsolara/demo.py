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
    p = Plot(
        # tools=TOOLS,
        toolbar_location="above",
        x_range=DataRange1d(),
        y_range=DataRange1d(),
        # height_policy='max',
        width_policy="max",
        output_backend=
        "webgl",  # for performance, will fallback to HTML5 if unsupported
        lod_factor=2000,
        lod_interval=300,
        lod_threshold=1000,
        lod_timeout=2000,
    )

    # generate axes
    xaxis = LinearAxis(axis_label=plotstate.x.value)
    yaxis = LinearAxis(axis_label=plotstate.y.value)
    p.add_layout(xaxis, "below")
    p.add_layout(yaxis, "left")
    grid_x = Grid(dimension=0, ticker=xaxis.ticker)
    grid_y = Grid(dimension=1, ticker=yaxis.ticker)
    p.add_layout(grid_x)
    p.add_layout(grid_y)

    # generate scrool wheel zoom
    wz = WheelZoomTool()
    p.add_tools(wz)
    p.toolbar.active_scroll = wz
    p.toolbar.autohide = True

    # TODO: temp
    def check_categorical(x: str):
        return False

    if check_categorical(plotstate.color.value):
        mpr = CategoricalColorMapper
        mpr_kwargs = dict()
    else:
        mpr_kwargs = dict(
            low=z.min(),
            high=z.max(),
        )
        if plotstate.colorlog.value is not None:
            mpr = LogColorMapper
        else:
            # linear
            mpr = LinearColorMapper

    mapper = mpr(
        palette=plotstate.colormap.value,
        **mpr_kwargs,
    )

    # generate scatter points
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
    cb = ColorBar(color_mapper=mapper,
                  location=(5, 6),
                  title=plotstate.color.value)
    p.add_layout(cb, "right")

    # create hovertool, bound to figure object
    TOOLTIPS = [
        (plotstate.x.value, "$snap_x"),
        (plotstate.y.value, "$snap_y"),
        (plotstate.color.value, "@z"),
        ("sdss_id", "@sdss_id"),
    ]
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

    hover = HoverTool(
        tooltips=TOOLTIPS,
        visible=False,
    )
    p.add_tools(hover)

    # add double click to open target page
    cb = CustomJS(
        args=dict(source=source),
        code=
        """window.open(`https://data.sdss.org/zora/target/${source.data.sdss_id[source.inspected.indices[0]]}`, '_blank').focus();""",
    )
    tap = TapTool(
        behavior="inspect",
        callback=cb,
        gesture="doubletap",
    )
    p.add_tools(tap)

    # add selection tools
    pantool = PanTool()
    p.add_tools(pantool)
    box_select = BoxSelectTool()
    p.add_tools(box_select)
    boxzoom = BoxZoomTool()
    p.add_tools(boxzoom)
    reset = ResetTool()
    p.add_tools(reset)

    with sl.Card():
        FigureBokeh(
            p,
            dependencies=[
                plotstate.x.value, plotstate.y.value, plotstate.color.value
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
