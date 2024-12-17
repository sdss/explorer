import traitlets as t
import os
import json
from urllib.parse import parse_qs
from typing import Optional

import solara as sl
from solara.lab import Menu
import reacton.ipyvuetify as rv
import reacton as r
import ipyvuetify as v
import ipywidgets as widgets

from sdss_explorer.pages.dataclass.state import State
from sdss_explorer.pages.util.io import export_layout, export_subset

from ...dataclass import SubsetState, GridState, Alert

from .plots import show_plot, index_context
from ..dialog import Dialog


class GridLayout(v.VuetifyTemplate):
    """
    A draggable & resizable grid layout which can be dragged via a toolbar.

    Arguably, this should use solara's components directly, but it
    doesn't function correctly with "component_vue" decorator.
    """

    template_file = os.path.join(os.path.dirname(__file__),
                                 "../../../vue/gridlayout_toolbar.vue")
    gridlayout_loaded = t.Bool(False).tag(sync=True)
    items = t.Union([t.List(), t.Dict()],
                    default_value=[]).tag(sync=True,
                                          **widgets.widget_serialization)
    grid_layout = t.List(default_value=[]).tag(sync=True)
    draggable = t.CBool(True).tag(sync=True)
    resizable = t.CBool(True).tag(sync=True)


GridDraggableToolbar = r.core.ComponentWidget(GridLayout)


@sl.component()
def ViewCard(type, i, **kwargs):

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

    index_context.provide(i)  # used to access height data for dynamic resize
    show_plot(type, lambda: remove(i), **kwargs)  # plot shower

    return


def add_view(type, layout: Optional[dict] = None, **kwargs):
    """Add a view to the grid. Layout can be parsed as a pre-made dict"""
    if layout is None:
        if len(GridState.grid_layout.value) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "w": 12, "moved": False}
        else:
            prev = GridState.grid_layout.value[-1]
        # TODO: better height logic
        if type == "stats":
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
    layout.update({'i': i})

    # add and update state vars
    GridState.grid_layout.value.append(layout)
    GridState.index.value += 1

    GridState.objects.value = GridState.objects.value + [
        ViewCard(type, i, **kwargs)
    ]


@sl.component()
def ObjectGrid():

    def reset_layout():
        GridState.index.value = 0
        GridState.grid_layout.value = []
        GridState.objects.value = []

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

    # NOTE: workaround for reactive monitoring of n subsets
    def update_n_subsets():
        return len(SubsetState.subsets.value)

    n_subsets = sl.use_memo(
        update_n_subsets,
        dependencies=[
            SubsetState.subsets.value,
        ],
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
                        #sl.Button(
                        #    label="delta2d",
                        #    on_click=lambda: add_view("delta2d"),
                        #    disabled=True if n_subsets <= 1 else False,
                        #),
                    ]
            rv.Spacer()

            # import/export app state UI
            impmenu, set_impmenu = sl.use_state(False)
            expmenu, set_expmenu = sl.use_state(False)
            with Dialog(open=impmenu,
                        ok=None,
                        ok_enable=False,
                        title='Import a layout JSON',
                        cancel='close',
                        max_width=960,
                        on_cancel=lambda *_: set_impmenu(False)):

                def parse_json():
                    # first, readd all virtual columns
                    # TODO

                    # second, create/add all plots with states and their according layout

                    return

                sl.FileDrop(label='Drop file here', on_file=parse_json)

            with Dialog(open=expmenu,
                        ok=None,
                        ok_enable=False,
                        cancel='close',
                        max_width=960,
                        on_cancel=lambda *_: set_expmenu(False)):

                def make_json() -> str:
                    """Creates JSON for file export."""
                    applayout = dict(subsets=dict())
                    for name, subset in SubsetState.subsets.value.items():
                        applayout['subsets'][name] = export_subset(subset)
                    applayout['views'] = export_layout(GridState)

                    return json.dumps(applayout)

                # TODO: should we add UTC time to make it more unique?
                with sl.FileDownload(make_json, f'layout-{State.uuid}.json'):
                    sl.Button('click me',
                              icon_name='mdi-cloud-download-outline',
                              outlined=False)

            btn2 = sl.Button(
                'Layout settings',
                outlined=False,
                icon_name='mdi-database-settings',
            )
            with Menu(activator=btn2):
                with rv.List(dense=True, ):
                    with rv.ListItem():
                        with rv.ListItemContent():
                            sl.Button('Import',
                                      outlined=False,
                                      on_click=lambda *_: set_impmenu(True),
                                      icon_name='mdi-application-import')
                    with rv.ListItem():
                        with rv.ListItemContent():
                            sl.Button('Export',
                                      outlined=False,
                                      on_click=lambda *_: set_expmenu(True),
                                      icon_name='mdi-application-export')
                    with rv.ListItem():
                        with rv.ListItemContent():
                            sl.Button(
                                'Reset',
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
    return main
