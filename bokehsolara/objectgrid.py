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

from state import plotstate, df
from plots import Scatter, Heatmap

dark = True


class GridLayout(v.VuetifyTemplate):
    """
    A draggable & resizable grid layout which can be dragged via a toolbar.

    Arguably, this should use solara's components directly, but it
    doesn't function correctly with "component_vue" decorator.
    """

    template_file = os.path.join(os.path.dirname(__file__),
                                 "gridlayout_toolbar.vue")
    gridlayout_loaded = t.Bool(False).tag(sync=True)
    items = t.Union([t.List(), t.Dict()],
                    default_value=[]).tag(sync=True,
                                          **widgets.widget_serialization)
    grid_layout = t.List(default_value=[]).tag(sync=True)
    draggable = t.CBool(True).tag(sync=True)
    resizable = t.CBool(True).tag(sync=True)


GridDraggableToolbar = r.core.ComponentWidget(GridLayout)


class GridState:
    index = sl.reactive(0)
    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    states = sl.reactive([])


def show_plot(plottype, remover, *args, **kwargs):
    with rv.Card(
            class_="grey darken-3" if dark else "grey lighten-3",
            style_="width: 100%#; height: 100%",
    ):
        with rv.CardText():
            with sl.Column(
                    classes=["grey darken-3" if dark else "grey lighten-3"]):
                if plottype == "heatmap":
                    Heatmap()
                else:
                    Scatter()
                btn = sl.Button(
                    icon_name="mdi-settings",
                    outlined=False,
                    classes=["grey darken-3" if dark else "grey lighten-3"],
                )
                with Menu(activator=btn, close_on_content_click=False):
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
                        with sl.Columns([1, 1]):
                            sl.Select(
                                label="color",
                                value=plotstate.color,
                                values=df.get_column_names(),
                            )
                            sl.Select(
                                label="bintype",
                                value=plotstate.bintype,
                                values=[
                                    "count", "mean", "min", "max", "median"
                                ],
                            )
                        sl.Select(
                            label="bintype",
                            value=plotstate.colormap,
                            values=colormaps,
                        )
                        with sl.Columns([1, 1]):
                            with sl.Column():
                                sl.Checkbox(label="xlog", value=plotstate.xlog)
                                sl.Checkbox(label="ylog", value=plotstate.ylog)
                            with sl.Column():
                                sl.Checkbox(label="xflip",
                                            value=plotstate.flipx)
                                sl.Checkbox(label="yflip",
                                            value=plotstate.flipy)
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=remover,
                        )


@sl.component()
def ViewCard(plottype, i, **kwargs):

    def remove(i):
        """
        i: unique identifier key, position in objects list
        q: specific, adaptive index in grid_objects (position dict)
        """
        # find where in grid_layout has key (i)
        for n, obj in enumerate(GridState.grid_layout.value):
            if obj["i"] == i:
                q = n
                break

        # cut layout and states at that spot
        GridState.grid_layout.value = (GridState.grid_layout.value[:q] +
                                       GridState.grid_layout.value[q + 1:])
        GridState.states.value = (GridState.states.value[:q] +
                                  GridState.states.value[q + 1:])

        # replace the object in object list with a dummy renderable
        # INFO: cannot be deleted because it breaks all renders
        GridState.objects.value[i] = rv.Card()

    show_plot(plottype, lambda: remove(i), **kwargs)  # plot shower

    return


def add_view(plottype, layout: Optional[dict] = None, **kwargs):
    """Add a view to the grid. Layout can be parsed as a pre-made dict"""
    if layout is None:
        if len(GridState.grid_layout.value) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "w": 12, "moved": False}
        else:
            prev = GridState.grid_layout.value[-1]
        # TODO: better height logic
        if plottype == "stats":
            height = 7
        else:
            height = 10
        # horizontal or vertical offset depending on width
        if 12 - prev["w"] - prev["x"] >= 6:
            # beside
            x = prev["x"] + 6
            y = prev["y"]
        else:
            # the row below
            x = 0
            y = prev["y"] + prev["h"] + 4
        layout = {
            "x": x,
            "y": y,
            "w": 6,
            "h": height,
            "moved": False,
        }

    # always update with current index
    i = GridState.index.value
    layout.update({"i": i})

    # add and update state vars
    GridState.grid_layout.value.append(layout)
    GridState.index.value += 1

    GridState.objects.value = GridState.objects.value + [
        ViewCard(plottype, i, **kwargs)
    ]


@sl.component()
def ObjectGrid():

    def set_grid_layout(data):
        GridState.grid_layout.value = data

    # WARNING: this is a janky workaround to a solara bug where
    # this will likely have to be changed in future.
    # BUG: it appears to incorrectly NOT reset the grid_layout reactive between different user instances/dev reset
    # don't know what's happening, but it appears to run some threads
    # below fix via thread solves it
    def monitor_grid():
        """Check to ensure length of layout spec is not larger than the number of objects.

        Solves a solara bug where global reactives do not appear to reset."""

        if len(GridState.objects.value) != len(GridState.grid_layout.value):
            while len(GridState.grid_layout.value) > len(
                    GridState.objects.value):
                GridState.grid_layout.value.pop(-1)
            GridState.index.value = len(GridState.objects.value)

    sl.use_thread(
        monitor_grid,
        dependencies=[GridState.objects.value, GridState.grid_layout.value],
    )

    with sl.Column(style={"width": "100%"}) as main:
        with sl.Row():
            btn = sl.Button(
                "Add View",
                outlined=False,
                icon_name="mdi-image-plus",
            )
            with Menu(activator=btn):
                with sl.Column(gap="0px"):
                    [
                        sl.Button(label="histogram",
                                  on_click=lambda: add_view("histogram")),
                        sl.Button(label="heatmap",
                                  on_click=lambda: add_view("heatmap")),
                        sl.Button(label="stats",
                                  on_click=lambda: add_view("stats")),
                        sl.Button(label="scatter",
                                  on_click=lambda: add_view("scatter")),
                        sl.Button(label="skyplot",
                                  on_click=lambda: add_view("skyplot")),
                        # TODO: fix delta2d
                        # BUG: delta2d is currently broken in many ways i need to fix
                        # sl.Button(
                        #    label="delta2d",
                        #    on_click=lambda: add_view("delta2d"),
                        #    disabled=True if n_subsets <= 1 else False,
                        # ),
                    ]
            rv.Spacer()
            sl.lab.ThemeToggle()

        GridDraggableToolbar(
            items=GridState.objects.value,
            grid_layout=GridState.grid_layout.value,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=True,
        )
    return main
