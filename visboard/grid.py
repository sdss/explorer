import traitlets as t
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

    Arguably, this should use solara, but it doesn't function correctly with "component_vue" decorator.
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


@sl.component
def ViewCard(type, del_func):
    with rv.Card(style_=" width: 100%; height: 100%") as main:
        if type == "table":
            with rv.CardText():
                with sl.Column():
                    DFView()
        else:
            state = PlotState()
            with rv.CardText():
                with sl.Column():
                    show_plot(type, state)
                btn = sl.Button(icon_name="mdi-settings", block=True)
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        show_settings(type, state)
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=del_func,
                        )

    return main


@sl.component
def ObjectGrid():
    objects, set_objects = sl.use_state([])
    grid_layout, set_grid_layout = sl.use_state([])

    def delete_card(i):
        set_grid_layout(grid_layout[0:i] + objects[i:])
        set_objects(objects[0:i] + objects[i:])

    def add_view(objects, type):
        if len(grid_layout) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "i": -1, "moved": False}
        else:
            prev = grid_layout[-1]
        # set height based on type
        if type == "table":
            height = 10
        elif type == "skyplot" or type == "scatter":
            height = 20
        else:
            height = 12
        grid_layout.append({
            "x": prev["x"],
            "y": prev["y"] + prev["h"] + 4,
            "w": 8,
            "h": height,
            "i": prev["i"] + 1,
            "moved": False,
        })

        set_objects(
            objects +
            [ViewCard(type, lambda: delete_card(grid_layout[-1]["i"]))])

    def add_histogram():
        add_view(objects, "histogram")

    def add_histogram2d():
        add_view(objects, "histogram2d")

    def add_scatter():
        add_view(objects, "scatter")

    def add_skyplot():
        add_view(objects, "skyplot")

    def add_table():
        add_view(objects, "table")

    def reset_layout():
        set_grid_layout([])
        set_objects([])

    with sl.Column() as main:
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
            sl.Button(color="yellow",
                      icon_name="mdi-refresh",
                      on_click=reset_layout)
        print(grid_layout)
        GridDraggableToolbar(
            items=objects,
            grid_layout=grid_layout,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=True,
        )
    return main
