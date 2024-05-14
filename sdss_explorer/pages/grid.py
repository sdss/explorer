import traitlets as t
import os

import solara as sl
from solara.lab import Menu
import reacton.ipyvuetify as rv
import reacton as r
import ipyvuetify as v
import ipywidgets as widgets

from .plots import show_plot
from .dataframe import show_table, DescribeDF
from .state import State


class GridLayout(v.VuetifyTemplate):
    """
    A draggable & resizable grid layout which can be dragged via a toolbar.

    Arguably, this should use solara's components directly, but it
    doesn't function correctly with "component_vue" decorator.
    """

    template_file = os.path.join(os.path.dirname(__file__),
                                 "../vue/gridlayout_toolbar.vue")
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
        """
        i: unique identifier key, position in objects list
        q: specific, adaptive index in grid_objects (position dict)
        """
        # find where in grid_layout has key (i)
        for n, obj in enumerate(GridState.grid_layout.value):
            if obj["i"] == i:
                q = n
                break

        # cut layout at that spot
        GridState.grid_layout.value = (GridState.grid_layout.value[:q] +
                                       GridState.grid_layout.value[q + 1:])

        # replace the object in object list with a dummy renderable
        # INFO: cannot be deleted because it breaks all renders
        GridState.objects.value[i] = rv.Card()

    if type != "stats":
        show_plot(type, lambda: remove(i))
    else:
        DescribeDF(lambda: remove(i))

    return


@sl.component
def ObjectGrid():

    def reset_layout():
        GridState.index = 0
        GridState.grid_layout.value = []
        GridState.objects.value = []

    def set_grid_layout(data):
        GridState.grid_layout.value = data

    def add_view(type):
        if len(GridState.grid_layout.value) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "moved": False}
        else:
            prev = GridState.grid_layout.value[-1]
        # set height based on type
        if type == "stats":
            height = 8
        else:
            height = 12
        i = GridState.index
        GridState.grid_layout.value.append({
            "x": prev["x"],
            "y": prev["y"] + prev["h"] + 4,
            "w": 8,
            "h": height,
            "i": i,
            "maxH": height,
            "minH": height,
            "moved": False,
        })
        GridState.index += 1

        GridState.objects.value = GridState.objects.value + [ViewCard(type, i)]

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
                                  on_click=lambda: add_view("aggregated")),
                        sl.Button(label="stats",
                                  on_click=lambda: add_view("stats")),
                        sl.Button(label="scatter",
                                  on_click=lambda: add_view("scatter")),
                        sl.Button(label="skyplot",
                                  on_click=lambda: add_view("skyplot")),
                        sl.Button(
                            label="delta2d",
                            on_click=lambda: add_view("delta2d"),
                            disabled=True
                            if len(State.subset_names.value) <= 1 else False,
                        ),
                    ]
            rv.Spacer()
            # sl.Button(
            #    color="yellow",
            #    icon_name="mdi-refresh",
            #    classes=["black--text"],
            #    on_click=reset_layout,
            # )
        GridDraggableToolbar(
            items=GridState.objects.value,
            grid_layout=GridState.grid_layout.value,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=True,
        )
    return main
