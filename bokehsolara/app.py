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
from bokeh.models import BoxSelectTool, ColorBar, LinearColorMapper, HoverTool
from bokeh.models import CustomJS
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu

from objectgrid import ObjectGrid
from state import df
from plots import LIGHTTHEME, DARKTHEME
from editor import ExprEditor
from figurebokeh import BokehLoaded


@sl.component
def Page():
    dark = sl.lab.use_dark_effective()
    loaded = sl.use_reactive(False)
    output_notebook(hide_banner=True)
    ExprEditor()
    ObjectGrid()

    # if df is not None:
    # else:
    #    sl.Info("help")
