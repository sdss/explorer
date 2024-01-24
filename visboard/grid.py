import traitlets as t
from typing import List, Dict, Union, Callable
import os

import solara as sl
from solara.lab import Menu
import reacton.ipyvuetify as rv
import reacton as r
import ipyvuetify as v
import ipywidgets as widgets

from plots import show_plot
from plot_settings import show_settings
from state import PlotState
from dataframe import DFView


class GridLayout(v.VuetifyTemplate):
    """
    A draggable & resizable grid layout which can be dragged via a toolbar.

    Arguably, this should use solara's components directly, but it doesn't function correctly with "component_vue" decorator.
    """

    template_file = os.path.join(os.path.dirname(__file__),
                                 "vue/gridlayout_toolbar.vue")
    gridlayout_loaded = t.Bool(False).tag(sync=True)
    items = t.Union([t.List(), t.Dict()],
                    default_value=[]).tag(sync=True,
                                          **widgets.widget_serialization)
    grid_layout = t.List(default_value=[]).tag(sync=True)
    draggable = t.CBool(True).tag(sync=True)
    resizable = t.CBool(True).tag(sync=True)


GridDraggableToolbar = r.core.ComponentWidget(GridLayout)


class GridState:
    """
    Class holding current state of grid.
    """

    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    index = 0


@sl.component
def ViewCard(type, i):

    def remove(i):
        # find where in grid_layout has this item no i
        q = int()
        for n, obj in enumerate(GridState.grid_layout.value):
            if obj["i"] == i:
                q = n
                break
        # cut layout at that spot, objects not cut because of how vue selects item to render
        GridState.grid_layout.value = (GridState.grid_layout.value[:q] +
                                       GridState.grid_layout.value[q + 1:])
        # replace the object with a dummy card
        GridState.objects.value[q] = rv.Card()

    with rv.Card(class_="grey darken-3",
                 style_="width: 100%; height: 100%") as main:
        state = PlotState()
        with rv.CardText():
            with sl.Column(classes=["grey darken-3"]):
                if type == "table":
                    DFView()
                else:
                    show_plot(type, state)
                btn = sl.Button(icon_name="mdi-settings",
                                outlined=False,
                                classes=["grey darken-3"])
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        show_settings(type, state)
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=lambda: remove(i),
                        )

    return main


@sl.component
def ObjectGrid():

    def set_grid_layout(data):
        GridState.grid_layout.value = data

    def add_view(type):
        if len(GridState.grid_layout.value) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "moved": False}
        else:
            prev = GridState.grid_layout.value[-1]
        # set height based on type
        if type == "table":
            height = 10
        else:
            height = 12
        i = GridState.index
        GridState.grid_layout.value.append({
            "x": prev["x"],
            "y": prev["y"] + prev["h"] + 4,
            "w": 8,
            "h": height,
            "i": i,
            "moved": False,
        })
        GridState.index += 1

        GridState.objects.value = GridState.objects.value + [ViewCard(type, i)]

    def add_histogram():
        add_view("histogram")

    def add_histogram2d():
        add_view("histogram2d")

    def add_scatter():
        add_view("scatter")

    def add_skyplot():
        add_view("skyplot")

    def add_table():
        add_view("table")

    def reset_layout():
        GridState.index = 0
        GridState.grid_layout.value = []
        GridState.objects.value = []

    with sl.Column(style={"width": "100%"}):
        with sl.Row():
            btn = sl.Button("Add View",
                            outlined=False,
                            icon_name="mdi-image-plus")
            with Menu(activator=btn):
                with sl.Column(gap="0px"):
                    [
                        sl.Button(label="histogram", on_click=add_histogram),
                        sl.Button(label="aggregated",
                                  on_click=add_histogram2d),
                        sl.Button(label="table", on_click=add_table),
                        sl.Button(label="scatter", on_click=add_scatter),
                        sl.Button(label="skyplot", on_click=add_skyplot),
                    ]
            rv.Spacer()
            sl.Button(
                color="yellow",
                icon_name="mdi-refresh",
                classes=["black--text"],
                on_click=reset_layout,
            )
        GridDraggableToolbar(
            items=GridState.objects.value,
            grid_layout=GridState.grid_layout.value,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=True,
        )
    print(GridState.objects.value)
    return
