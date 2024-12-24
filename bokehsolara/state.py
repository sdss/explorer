import datashader as ds
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

df = vx.example()[:100_000]

TOOLS = 'pan,wheel_zoom,box_zoom,reset,save'

colormaps = [x for x in colormaps if '256' in x]


def gen_tooltips(state):
    """Helper function to generate tooltips"""
    tooltips = []
    tooltips.append((state.x.value, '$x'))
    tooltips.append((state.y.value, '$y'))
    if plotstate.type.value == 'heatmap':
        tooltips.append((state.bintype.value, '@z'))

    return tooltips


class plotstate:
    type = sl.reactive('heatmap')
    x = sl.reactive('x')
    y = sl.reactive('y')
    bintype = sl.reactive('mean')
    color = sl.reactive('FeH')
    colormap = sl.reactive('Inferno256')
    nbins = sl.reactive(101)
    last_hovered_id = sl.reactive(cast(int, None))
