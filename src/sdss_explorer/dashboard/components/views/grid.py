import json
import logging
import os
from datetime import datetime
from typing import Optional

from bokeh.io import output_notebook
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

logger = logging.getLogger("dashboard")


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
    main = show_plot(plottype, lambda: remove(i), **kwargs)  # plot shower

    logger.debug("returning viewcard now")
    return main


def add_view(plottype, layout: Optional[dict] = None, **kwargs):
    """Add a view to the grid. Layout can be parsed as a pre-made dict"""
    if layout is None:
        if len(GridState.grid_layout.value) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "w": 12, "moved": False}
        else:
            prev = GridState.grid_layout.value[-1]
        maxH = 40
        minH = 7
        if plottype == "stats":
            height = 7
        elif plottype == "targets":
            height = 9
            maxH = 9
            minH = 9
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
            "maxH": maxH,
            "minH": minH,
            "moved": False,
        }

    # always update with current index
    i = GridState.index.value
    layout.update({"i": i})

    # add and update state vars
    GridState.index.value += 1
    GridState.grid_layout.value = GridState.grid_layout.value + [layout]

    logger.debug("entering cardmake")
    card = ViewCard(plottype, i, **kwargs)
    logger.debug("got card")
    newlist = GridState.objects.value.copy() + [card]
    logger.debug("appended")
    GridState.objects.value = newlist
    logger.debug("set")
    logger.debug("append done, exiting")


@sl.component()
def ObjectGrid():
    impmenu, set_impmenu = sl.use_state(False)
    lockout, set_lockout = sl.use_state(False)
    areyousure, set_areyousure = sl.use_state(False)

    def reset_layout():
        GridState.index.value = 0
        GridState.grid_layout.value = []
        GridState.objects.value = []
        GridState.states.value = []
        GridState.index.value = 0

    def set_grid_layout(data):
        GridState.grid_layout.value = data

    def import_applayout(fileobj: FileInfo) -> None:
        """Converts JSON to app state and updates accordingly.

        Note:
            Function has to be here to serve state updates properly.

        Args:
            fileobj: the file data, loaded as a solara.FileInfo object.
        """
        # convert from json to dicts
        set_lockout(True)
        try:
            data = json.load(fileobj["file_obj"])
        except Exception as e:
            Alert.update("Import failed!", color="error")
            logger.debug(f"JSON load to import layout failed failed: {e}")
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
        for subset in subsets.values():
            subset["df"] = (State.df.value[State.df.value[
                f"(pipeline=='{subset.get('dataset')}')"]].copy().extract())
            subset["columns"] = State.columns.value[subset.get("dataset")]

        subsets_spawned = {k: Subset(**v) for k, v in subsets.items()}
        SubsetState.index.set(len(subsets))
        SubsetState.subsets.set(subsets_spawned)

        # finally, create/add all plots with states and their according layout
        layouts = data["views"]["layout"]
        states = data["views"]["states"]

        for layout, state in zip(layouts, states):
            try:
                logger.debug("adding view")
                logger.debug(layout)
                logger.debug(state)
                plottype = state.pop("plottype")
                add_view(plottype, layout=layout, **state)
            except Exception as e:
                Alert.update(f"JSON load of {fileobj['name']} failed!",
                             color="error")
                Alert.update
                logger.debug("failed to add view on import" + str(e))
                continue

        Alert.update("Layout imported successfully!", color="success")

        # unlock
        set_lockout(False)
        set_impmenu(False)

        return

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
                                    label="targets",
                                    on_click=lambda: add_view("targets"),
                                ),
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
            with sl.Tooltip(
                    "Import, export, and reset the layout (currently disabled)."
            ):
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
                                            disabled=True,
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
                                                disabled=True,
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
