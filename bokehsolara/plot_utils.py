import os
from typing import Callable, Optional, cast

from bokeh.models.grids import Grid
from bokeh.models.plots import Plot
from bokeh.models.ranges import DataRange1d, FactorRange
from bokeh.models.tools import WheelZoomTool
import ipyvuetify as v
import ipywidgets as widgets
import numpy as np
import reacton as r
import reacton.ipyvuetify as rv
import solara as sl
import traitlets as t
import vaex as vx
import xarray
from bokeh.io import output_notebook, curdoc, push_notebook
from bokeh.events import Reset
from bokeh.models.scales import LinearScale, LogScale, CategoricalScale
from bokeh.models import (
    BoxSelectTool,
    BoxZoomTool,
    LassoSelectTool,
    ColorBar,
    HoverTool,
    Scatter,
    ExamineTool,
    TapTool,
    PanTool,
    ResetTool,
)
from bokeh.models.mappers import (
    LinearColorMapper,
    LogColorMapper,
    CategoricalColorMapper,
)
from bokeh.models import CustomJS, OpenURL
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from bokeh.models.axes import CategoricalAxis, LogAxis, LinearAxis
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu
from bokeh.models.axes import Axis

from util import check_categorical


def add_all_tools(p: Plot, tooltips: Optional[str] = None):
    """Adds all basic tools, modifies plot's toolbar."""
    # create hovertool
    hover = HoverTool(
        tooltips=tooltips,
        visible=False,
    )

    # generate other tools
    pan = PanTool()
    boxzoom = BoxZoomTool()
    wz = WheelZoomTool()
    box_select = BoxSelectTool()
    lasoo = LassoSelectTool()
    reset = ResetTool()
    examine = ExamineTool()
    tools = [pan, boxzoom, box_select, lasoo, examine, hover, wz, reset]
    p.add_tools(*tools)
    p.toolbar.active_scroll = wz
    p.toolbar.autohide = True

    return tools


def generate_axes(plotstate, p: Plot):
    """Generates axes and corresponding grids for plots"""
    xaxis = LinearAxis(axis_label=generate_xlabel(plotstate))
    yaxis = LinearAxis(axis_label=generate_ylabel(plotstate))
    grid_x = Grid(dimension=0, ticker=xaxis.ticker, visible=True)
    grid_y = Grid(dimension=1, ticker=yaxis.ticker, visible=True)
    p.add_layout(xaxis, "below")
    p.add_layout(yaxis, "left")
    p.add_layout(grid_x, "center")
    p.add_layout(grid_y, "center")
    return p


def generate_color_mapper_bar(plotstate, z):
    """Get color mapper and colorbar for colorbar plots"""
    if check_categorical(plotstate.color.value):
        mpr = CategoricalColorMapper
        mpr_kwargs = dict()  # TODO: catagorical mapper
    else:
        mpr_kwargs = dict(
            low=z.min(),
            high=z.max(),
        )
        if plotstate.colorlog.value is not None:
            mpr = LogColorMapper
        else:
            mpr = LinearColorMapper
    mapper = mpr(
        palette=plotstate.colormap.value,
        **mpr_kwargs,
    )
    cb = ColorBar(color_mapper=mapper,
                  location=(5, 6),
                  title=plotstate.color.value)
    return mapper, cb


def generate_xlabel(plotstate) -> str:
    """Generates a x-axis label."""
    cond = plotstate.logx.value and not check_categorical(plotstate.x.value)
    return f"{'log(' if cond else ''}{plotstate.x.value}{')' if cond else ''}"


def generate_ylabel(plotstate) -> str:
    """Generates a y-axis label."""
    cond = plotstate.logy.value and not check_categorical(plotstate.y.value)
    return f"{'log(' if cond else ''}{plotstate.y.value}{')' if cond else ''}"


def generate_plot(plotstate):
    """Generates basic plot object with context menu, with object bindings"""
    # create menu
    menu = BokehMenu()
    menu.styles = {"color": "black", "font-size": "16px"}

    # generate main Plot model
    p = Plot(
        context_menu=menu,
        toolbar_location="above",
        x_range=DataRange1d(),
        x_scale=LinearScale(),
        y_range=DataRange1d(),
        y_scale=LinearScale(),
        # height_policy='max', # NOTE: doesn't work
        width_policy="max",
        reset_policy=
        "event_only",  # NOTE: we handle resets ourselves bc changing scales crashes it
        output_backend=
        "webgl",  # for performance, will fallback to HTML5 if unsupported
        lod_factor=20000,
        lod_interval=300,
        lod_threshold=1000,
        lod_timeout=10000,
    )
    name = "menu-propogate"
    items = [
        ActionItem(label="View table of selected targets",
                   disabled=True,
                   name="menu-table"),
        ActionItem(
            label="Propagate selection to new subset",
            disabled=True,
            name="menu-propogate",
        ),
        ActionItem(label="Clear selection", disabled=True, name="menu-clear"),
        ActionItem(
            label="Reset plot",
            action=CustomJS(args=dict(p=p), code="""p.reset.emit()"""),
        ),
    ]
    menu.update(items=items)

    return p, menu


def calculate_range(plotstate, df, col, start, end):
    """Fetches a new reset-like start/end value based on the flip, log, and column"""
    pass
    # expr = df[col] if
    # range = abs(.min()[()] - df[col].max()[()])
