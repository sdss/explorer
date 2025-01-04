import json
import logging
import os
from datetime import datetime
from typing import Optional

import ipyvuetify as v
import ipywidgets as widgets
import reacton as r
import reacton.ipyvuetify as rv
import solara as sl
import traitlets as t
from solara.components.file_drop import FileInfo
from solara.lab import Menu

from ...dataclass import Alert, GridState, State, Subset, SubsetState, VCData
from ...util.io import export_layout, export_subset, export_vcdata
from ..dialog import Dialog
from .plots import index_context, show_plot

logger = logging.getLogger("sdss_explorer")


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

    index_context.provide(i)  # used to access height data for dynamic resize
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
    impmenu, set_impmenu = sl.use_state(False)
    lockout, set_lockout = sl.use_state(False)
    areyousure, set_areyousure = sl.use_state(False)

    def reset_layout():
        GridState.index.value = 0
        GridState.grid_layout.value = []
        GridState.objects.value = []
        GridState.index.value = 0

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

    def export_applayout() -> str:
        """Creates JSON for file export."""
        applayout = dict(subsets=dict())
        for name, subset in SubsetState.subsets.value.items():
            applayout["subsets"][name] = export_subset(subset)
        applayout["views"] = export_layout(GridState)
        applayout["virtual_columns"] = export_vcdata(VCData)

        return json.dumps(applayout)

    with sl.Column(style={"width": "100%"}) as main:
        with sl.Row():
            btn = sl.Button(
                "Add View",
                outlined=False,
                icon_name="mdi-image-plus",
            )
            with sl.Tooltip("Add a plot."):
                with sl.Column():
                    with Menu(activator=btn):
                        with sl.Column(gap="0px"):
                            [
                                sl.Button(
                                    label="histogram",
                                    on_click=lambda: add_view("histogram"),
                                ),
                                sl.Button(
                                    label="heatmap",
                                    on_click=lambda: add_view("heatmap"),
                                ),
                                sl.Button(label="stats",
                                          on_click=lambda: add_view("stats")),
                                sl.Button(
                                    label="scatter",
                                    on_click=lambda: add_view("scatter"),
                                ),
                                sl.Button(
                                    label="skyplot",
                                    on_click=lambda: add_view("skyplot"),
                                ),
                                # TODO: fix delta2d
                                # BUG: delta2d is currently broken in many ways i need to fix
                                # sl.Button(
                                #    label="delta2d",
                                #    on_click=lambda: add_view("delta2d"),
                                #    disabled=True if n_subsets <= 1 else False,
                                # ),
                            ]
            rv.Spacer()

            # import/export app state UI
            with Dialog(
                    open=impmenu,
                    ok=None,
                    ok_enable=False,
                    title="Import a layout JSON",
                    cancel="close",
                    max_width=960,
                    on_cancel=lambda *_: set_impmenu(False),
            ):

                def import_applayout(fileobj: FileInfo) -> None:
                    """Converts JSON to app state and updates accordingly.
                    Function has to be here to serve state updates properly."""
                    # convert from json to dicts
                    set_lockout(True)
                    try:
                        data = json.load(fileobj["file_obj"])
                    except Exception as e:
                        Alert.update(f"JSON load of {fileobj['name']} failed!",
                                     color="error")
                        logger.debug(
                            f"JSON load of {fileobj['name']} failed: {e}")
                        set_lockout(False)
                        set_impmenu(False)
                        return

                    # wipe current layout & delete all virtual columns
                    reset_layout()
                    for name in VCData.columns.value.keys():
                        VCData.delete_column(name)

                    # now, readd all virtual columns
                    for name, expr in data["virtual_columns"].items():
                        VCData.add_column(name, expr)

                    # second, readd all subsets
                    subsets = data["subsets"]
                    subsets_spawned = {
                        k: Subset(**v)
                        for k, v in subsets.items()
                    }
                    SubsetState.index.set(len(subsets))
                    SubsetState.subsets.set(subsets_spawned)

                    # finally, create/add all plots with states and their according layout
                    layouts = data["views"]["layout"]
                    states = data["views"]["states"]
                    for layout, state in zip(layouts, states):
                        add_view(layout=layout, **state)

                    Alert.update("Layout imported successfully!",
                                 color="success")

                    # unlock
                    set_lockout(False)
                    set_impmenu(False)

                    return

                sl.FileDrop(label="Drop file here", on_file=import_applayout)

                # lockout via indeterminate loading circle and overlay (ui is uninteractable)
                if lockout:
                    with rv.Overlay():
                        rv.ProgressCircular(indeterminate=True)

            # TODO: remove this dialog, just make the export dump to file and pass to user
            def close_areyousure(*ignore_args):
                reset_layout()
                set_areyousure(False)

            Dialog(
                open=areyousure,
                title="Are you sure you want to reset the layout?",
                max_width=480,
                ok="Yes",
                cancel="No",
                close_on_ok=False,
                on_ok=close_areyousure,
                on_cancel=lambda *_: set_areyousure(False),
            )

            btn2 = sl.Button(
                "Layout options",
                outlined=False,
                icon_name="mdi-database-settings",
            )
            with sl.Tooltip("Import, export, and reset the layout."):
                with sl.Column():
                    with Menu(activator=btn2):
                        with rv.List(dense=True, ):
                            with rv.ListItem():
                                with rv.ListItemContent():
                                    with sl.Tooltip(
                                            "Import a previously exported layout."
                                    ):
                                        sl.Button(
                                            "Import",
                                            outlined=False,
                                            on_click=lambda *_: set_impmenu(
                                                True),
                                            icon_name="mdi-application-import",
                                        )
                            with rv.ListItem():
                                with rv.ListItemContent():
                                    with sl.FileDownload(
                                            export_applayout,
                                            f"zoraLayout-{datetime.now().strftime('%Y-%m-%d_%H:%M')}-{State.uuid}.json",
                                    ):
                                        with sl.Tooltip(
                                                "Export the current layout to a file."
                                        ):
                                            sl.Button(
                                                "Export",
                                                outlined=False,
                                                icon_name=
                                                "mdi-application-export",
                                                style={"width": "100%"},
                                            )
                            with rv.ListItem():
                                with rv.ListItemContent():
                                    with sl.Tooltip(
                                            "Reset and delete all open views."
                                    ):
                                        sl.Button(
                                            "Reset",
                                            color="yellow",
                                            icon_name="mdi-refresh",
                                            classes=["black--text"],
                                            on_click=lambda *_: set_areyousure(
                                                True),
                                        )
        GridDraggableToolbar(
            items=GridState.objects.value,
            grid_layout=GridState.grid_layout.value,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=True,
        )
    return main
