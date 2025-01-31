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
from bokeh.models import BoxSelectTool, ColorBar, LinearColorMapper, HoverTool
from bokeh.models import CustomJS
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu


class plotstate:
    type = sl.reactive("heatmap")
    x = sl.reactive("x")
    y = sl.reactive("y")
    bintype = sl.reactive("mean")
    color = sl.reactive("FeH")
    colormap = sl.reactive("Inferno256")
    nbins = sl.reactive(101)
    menu_item_id = sl.reactive(cast(str, None))
    last_hovered_id = sl.reactive(cast(int, None))


@sl.component()
def Page():
    df = vx.example()[:30_000]
    z = df[plotstate.color.value].values
    source = ColumnDataSource(
        data={
            "x": df[plotstate.x.value].values,
            "y": df[plotstate.y.value].values,
            "z": z,
            "sdss_id": df["L"].values,  # temp
        })

    # generate main figure
    p = figure(
        x_axis_label=plotstate.x.value,
        y_axis_label=plotstate.y.value,
        toolbar_location="above",
        width_policy="max",  # width works, height doesnt?
        active_scroll="wheel_zoom",  # default to scroll wheel for zoom
        output_backend=
        "webgl",  # for performance, will fallback to HTML5 if unsupported
    )
    mapper = LinearColorMapper(
        palette=plotstate.colormap.value,
        low=z.min(),
        high=z.max(),
    )

    # generate scatter points
    glyph = p.scatter(
        x="x",
        y="y",
        source=source,
        size=4,
        fill_color={
            "field": "z",
            "transform": mapper
        },
    )
    with sl.Card():
        FigureBokeh(p, dependencies=[plotstate.x.value, plotstate.y.value])
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
