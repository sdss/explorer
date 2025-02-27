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

df = vx.example()[:30_000]
data = np.array(["foo" if i < len(df) // 2 else "bar" for i in range(len(df))])
data[:10_000] = "teodddd"
data2 = np.array(
    ["lco25m" if i < len(df) // 3 else "apo25m" for i in range(len(df))])
df["category"] = data
df["category2"] = data2
df = df.materialize("category")
df = df.materialize("category2")


def gen_tooltips(state):
    """Helper function to generate tooltips"""
    tooltips = []
    tooltips.append((state.x.value, "$x"))
    tooltips.append((state.y.value, "$y"))
    if state.plottype.value == "heatmap":
        tooltips.append((state.bintype.value, "@z"))

    return tooltips


class GridState:
    index = sl.reactive(0)
    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    states = sl.reactive([])


class PlotState:
    """
    Combination of reactive states which instantiate a specific plot's settings/properties.
    Initializes based on keyword arguments.
    """

    def __init__(self, plottype, current_key, **kwargs):
        # subset and type states
        self.plottype = str(plottype)
        self.subset = sl.use_reactive(current_key)

        if "stats" in plottype:
            self.columns = sl.use_reactive(["g_mag", "bp_mag"])
        else:
            # common plot settings
            self.x = sl.use_reactive(kwargs.get("x", "x"))
            self.flipx = sl.use_reactive(kwargs.get("flipx", ""))
            self.flipy = sl.use_reactive(kwargs.get("flipy", ""))
            self.xmapping = dict()  # non-reactive
            self.ymapping = dict()  # non-reactive

            # moderately unique plot parameters/settings
            if plottype != "histogram":
                self.y = sl.use_reactive(kwargs.get("y", "y"))
                self.color = sl.use_reactive(kwargs.get("color", "FeH"))
                self.colormapping = dict()  # non-reactive
                self.colorscale = sl.use_reactive(
                    kwargs.get("colorscale", "Inferno256"))
                self.logcolor = sl.use_reactive(kwargs.get("logcolor", False))
            if plottype != "aggregated" and plottype != "skyplot":
                self.logx = sl.use_reactive(kwargs.get("logx", ""))
                self.logy = sl.use_reactive(kwargs.get("logy", ""))

            # statistics settings
            if plottype == "heatmap" or plottype == "histogram" or "delta" in plottype:
                self.nbins = sl.use_reactive(200)
                if plottype == "heatmap" or plottype == "delta2d":
                    self.bintype = sl.use_reactive(
                        kwargs.get("bintype", "mean"))
                else:
                    self.bintype = sl.use_reactive(
                        kwargs.get("bintype", "count"))

            # skyplot settings
            if plottype == "skyplot":
                self.geo_coords = sl.use_reactive(
                    kwargs.get("coords", "celestial"))
                self.projection = sl.use_reactive(
                    kwargs.get("projection", "hammer"))

            # delta view settings
            if "delta" in plottype:
                # NOTE: view can only be created when there are 2 subsets
                self.subset_b = sl.use_reactive(current_key)
            # all lookup data for plottypes
            # TODO: move this lookup data elsewhere to reduce the size of the plotstate objects
        self.Lookup = dict(
            norms={
                None, "percent", "probability", "density",
                "probability density"
            },
            bintypes={
                "count",
                "mean",
                "median",
                "sum",
                "min",
                "max",
                "mode",
                "cov",
                "covar",
            },
            colorscales=colormaps,
            binscales={None, "log1p", "log10"},
            projections={
                "albers",
                "aitoff",
                "azimuthal equal area",
                "equal earth",
                "hammer",
                "mollweide",
                "mt flat polar quartic",
            },
        )

    def swap_axes(self):
        # saves current to p and q
        p = self.x.value
        q = self.y.value
        self.x.value = q
        self.y.value = p
