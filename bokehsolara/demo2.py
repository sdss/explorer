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
from bokeh.io import output_notebook, curdoc
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

from bokeh.transform import linear_cmap, log_cmap, factor_cmap
from plot_utils import (
    add_all_tools,
    generate_axes,
    generate_color_mapper_bar,
    generate_plot,
)
from plot_themes import darkprops as props
from state import plotstate, df
from bokeh.io import show
from plots import ScatterPlot


@sl.component()
def Page():
    output_notebook(hide_banner=True)
    active = sl.use_reactive(False)

    with sl.GridFixed(columns=1):
        with sl.Card(elevation=0):
            if active.value:
                ScatterPlot()
    with sl.Card(margin=0):
        sl.Button(label="spawn", on_click=lambda *ignore: active.set(True))
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
            sl.Checkbox(label="logx", value=plotstate.logx)
            sl.Checkbox(label="logy", value=plotstate.logy)
            sl.lab.ThemeToggle()


if __name__ == "__main__":
    Page()
