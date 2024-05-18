"""Plot settings menus"""

import solara as sl
from solara.components.card import Card
from solara.components.columns import Columns

from .state import State


def show_settings(type, state):
    """Wrapper to case switch logic for menus"""
    # plot controls
    if type == "scatter":
        return ScatterMenu(state)
    elif type == "histogram":
        return HistogramMenu(state)
    elif type == "heatmap":
        return HeatmapMenu(state)
    elif type == "skyplot":
        return SkymapMenu(state)
    elif type == "delta2d":
        return DeltaHeatmapMenu(state)


@sl.component()
def SkymapMenu(plotstate):
    """Settings for SkymapPlot"""
    columns = State.columns.value
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[State.subsets.value, State.columns.value],
    )
    with sl.Columns([1, 1]):
        with Card(margin=0):
            sl.Select(
                label="Subset",
                values=State.subsets.value,
                value=plotstate.subset,
            )
            with sl.Column():
                sl.ToggleButtonsSingle(value=plotstate.geo_coords,
                                       values=["celestial", "galactic"])
                sl.Select(
                    label="Projection",
                    value=plotstate.projection,
                    values=plotstate.Lookup["projections"],
                )
            with sl.Row():
                sl.Select(
                    label="Color",
                    values=columns,
                    value=plotstate.color,
                )
                sl.Select(
                    label="Colorscale",
                    values=plotstate.Lookup["colorscales"],
                    value=plotstate.colorscale,
                )
                sl.Select(
                    label="Color log",
                    values=plotstate.Lookup["binscales"],
                    value=plotstate.colorlog,
                )
        with Card(margin=0):
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)


@sl.component()
def ScatterMenu(plotstate):
    """Settings for ScatterPlot"""
    columns = State.columns.value
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[State.subsets.value, State.columns.value],
    )
    with sl.Card():
        sl.Select(
            label="Subset",
            values=State.subsets.value,
            value=plotstate.subset,
        )
        with sl.Columns([1, 1]):
            with sl.Column():
                with Columns([8, 8, 2], gutters_dense=True):
                    sl.Select(
                        "Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x,
                    )
                    sl.Select(
                        "Column y",
                        values=[
                            col for col in columns if col != plotstate.x.value
                        ],
                        value=plotstate.y,
                    )
                    sl.Button(
                        icon=True,
                        icon_name="mdi-swap-horizontal",
                        on_click=plotstate.swap_axes,
                    )
                with sl.Column():
                    sl.Select(
                        label="Color",
                        values=columns,
                        value=plotstate.color,
                    )
                    with sl.Row(gap="2px"):
                        sl.Select(
                            label="Colorscale",
                            values=plotstate.Lookup["colorscales"],
                            value=plotstate.colorscale,
                        )
                        sl.Select(
                            label="Color log",
                            values=plotstate.Lookup["binscales"],
                            value=plotstate.colorlog,
                        )
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                    sl.Switch(label="Log x", value=plotstate.logx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                    sl.Switch(label="Log y", value=plotstate.logy)


@sl.component()
def HistogramMenu(plotstate):
    """Settings for HistogramPlot"""
    columns = State.columns.value
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[State.subsets.value, State.columns.value],
    )

    sl.Select(
        label="Subset",
        values=State.subsets.value,
        value=plotstate.subset,
    )
    with sl.Columns([1, 1]):
        with Card(margin=0):
            with sl.Column():
                sl.Select(
                    "Column",
                    values=columns,
                    value=plotstate.x,
                )
        with Card(margin=0):
            sl.SliderInt(
                label="Number of Bins",
                value=plotstate.nbins,
                step=10,
                min=10,
                max=1e3,
            )
            sl.Select(
                label="Bintype",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype,
            )
    with Card(margin=0):
        with sl.Columns([1, 1, 1], style={"align-items": "center"}):
            sl.Switch(label="Log x", value=plotstate.logx)
            sl.Switch(label="Flip x", value=plotstate.flipx)
            sl.Switch(label="Log y", value=plotstate.logy)


@sl.component()
def HeatmapMenu(plotstate):
    """Settings for HeatmapPlot"""
    columns = State.columns.value
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[State.subsets.value, State.columns.value],
    )
    with sl.Columns([1, 1]):
        with Card(margin=0):
            sl.Select(
                label="Subset",
                values=State.subsets.value,
                value=plotstate.subset,
            )
            with Columns([3, 3, 1], gutters_dense=True):
                with sl.Column():
                    sl.Select(
                        "Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x,
                    )
                with sl.Column():
                    sl.Select(
                        "Column y",
                        values=[
                            col for col in columns if col != plotstate.x.value
                        ],
                        value=plotstate.y,
                    )
                sl.Button(
                    icon=True,
                    icon_name="mdi-swap-horizontal",
                    on_click=plotstate.swap_axes,
                )
            sl.Select(
                label="Colorscale",
                values=plotstate.Lookup["colorscales"],
                value=plotstate.colorscale,
            )
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
        with Card(margin=0):
            sl.SliderInt(
                label="Number of Bins",
                value=plotstate.nbins,
                step=2,
                min=2,
                max=250,
            )
            sl.Select(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype,
            )
            if str(plotstate.bintype.value) != "count":
                sl.Select(
                    label="Column to Bin",
                    values=columns,
                    value=plotstate.color,
                )
            sl.Select(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale,
            )


@sl.component()
def DeltaHeatmapMenu(plotstate):
    """Settings for DeltaHeatmapPlot"""
    columns = State.columns.value
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[State.subsets.value, State.columns.value],
    )
    with Card(margin=0):
        with sl.Columns([3, 3, 1]):
            sl.Select(
                label="Subset 1",
                values=[
                    subset for subset in State.subsets.value
                    if subset != plotstate.subset_b.value
                ],
                value=plotstate.subset,
            )
            sl.Select(
                label="Subset 2",
                values=[
                    subset for subset in State.subsets.value
                    if subset != plotstate.subset.value
                ],
                value=plotstate.subset_b,
            )
            sl.Button(
                icon=True,
                icon_name="mdi-swap-horizontal",
                on_click=plotstate.swap_subsets,
            )

    with sl.Columns([1, 1]):
        with Card(margin=0):
            with Columns([3, 3, 1], gutters_dense=True):
                with sl.Column():
                    sl.Select(
                        "Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x,
                    )
                with sl.Column():
                    sl.Select(
                        "Column y",
                        values=[
                            col for col in columns if col != plotstate.x.value
                        ],
                        value=plotstate.y,
                    )
                sl.Button(
                    icon=True,
                    icon_name="mdi-swap-horizontal",
                    on_click=plotstate.swap_axes,
                )
            sl.Select(
                label="Colorscale",
                values=plotstate.Lookup["colorscales"],
                value=plotstate.colorscale,
            )
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
        with Card(margin=0):
            sl.SliderInt(
                label="Number of Bins",
                value=plotstate.nbins,
                step=2,
                min=2,
                max=500,
            )
            sl.Select(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype,
            )
            if str(plotstate.bintype.value) != "count":
                sl.Select(
                    label="Column to Bin",
                    values=columns,
                    value=plotstate.color,
                )
            sl.Select(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale,
            )
