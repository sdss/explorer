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

df = vx.example()[:50_000]
df["category"] = np.array(
    ["foo" if i < len(df) // 2 else "bar" for i in range(len(df))])
df = df.materialize("category")


def gen_tooltips(state):
    """Helper function to generate tooltips"""
    tooltips = []
    tooltips.append((state.x.value, "$x"))
    tooltips.append((state.y.value, "$y"))
    if plotstate.type.value == "heatmap":
        tooltips.append((state.bintype.value, "@z"))

    return tooltips


class plotstate:
    plottype = sl.reactive("heatmap")
    x = sl.reactive("x")
    y = sl.reactive("y")
    logx = sl.reactive(False)
    logy = sl.reactive(False)
    flipx = sl.reactive(False)
    flipy = sl.reactive(False)
    bintype = sl.reactive("mean")
    color = sl.reactive("FeH")
    colormap = sl.reactive("Inferno256")
    colorlog = sl.reactive(cast(str, None))
    nbins = sl.reactive(101)
    menu_item_id = sl.reactive(cast(str, None))
    last_hovered_id = sl.reactive(cast(int, None))


class GridState:
    index = sl.reactive(0)
    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    states = sl.reactive([])
