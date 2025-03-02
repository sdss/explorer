"""Plot settings menus"""

import asyncio
import logging

import solara as sl
from reacton.ipyvuetify import ValueElement
from solara.components.card import Card
from solara.components.columns import Columns

from ...dataclass import SubsetState, Subset, VCData, PlotState
from ..sidebar.autocomplete import SingleAutocomplete, AutocompleteSelect

logger = logging.getLogger("dashboard")


def show_settings(type: str, plotstate: PlotState):
    """Wrapper to case switch logic for menus"""
    subset = SubsetState.subsets.value.get(plotstate.subset.value,
                                           Subset(name="temp"))
    columns = list(VCData.columns.value.keys()) + subset.columns
    sl.lab.use_task(
        plotstate.reset_values,
        dependencies=[
            subset.df,
            subset.dataset,
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            VCData.columns.value,
        ],
    )
    name, names = (
        subset.name,
        [ss.name for ss in SubsetState.subsets.value.values()],
    )

    # specific plot controls
    with sl.Column():
        SingleAutocomplete(
            label="Subset",
            values=names,
            value=name,
            on_value=plotstate.update_subset,
        )
        if (type == "stats") or (type == "targets"):
            TableMenu(plotstate)
        else:
            with sl.Columns([1, 1]):
                if type == "scatter":
                    ScatterMenu(plotstate, columns)
                elif type == "histogram":
                    HistogramMenu(plotstate, columns)
                elif type == "heatmap":
                    HeatmapMenu(plotstate, columns)
                CommonSettings(plotstate)
    return


def debounce(value, sleep: float = 0.1):
    """Generates a debouncer function"""

    async def debouncer():
        await asyncio.sleep(sleep)
        return value

    return debouncer


@sl.component
def CommonSettings(plotstate: PlotState) -> ValueElement:
    """Common plot settings, with debouncers"""
    plottype = plotstate.plottype
    logx = sl.use_reactive(getattr(plotstate, "logx").value)
    logy = sl.use_reactive(getattr(plotstate, "logy").value)
    flipx = sl.use_reactive(getattr(plotstate, "flipx").value)
    flipy = sl.use_reactive(getattr(plotstate, "flipy").value)
    logcolor = sl.use_reactive(getattr(plotstate, "logcolor").value)

    # debouncing values
    # BUG: non-threaded until https://github.com/widgetti/solara/issues/1011 is fixed
    db_logx = sl.lab.use_task(debounce(logx.value),
                              dependencies=[logx.value],
                              prefer_threaded=False)
    if db_logx.value == logx.value:
        plotstate.logx.set(db_logx.value)
    db_logy = sl.lab.use_task(debounce(logy.value),
                              dependencies=[logy.value],
                              prefer_threaded=False)
    if db_logy.value == logy.value:
        plotstate.logy.set(db_logy.value)
    db_flipx = sl.lab.use_task(debounce(flipx.value),
                               dependencies=[flipx.value],
                               prefer_threaded=False)
    if db_flipx.value == flipx.value:
        plotstate.flipx.set(db_flipx.value)
    db_flipy = sl.lab.use_task(debounce(flipy.value),
                               dependencies=[flipy.value],
                               prefer_threaded=False)
    if db_flipy.value == flipy.value:
        plotstate.flipy.set(db_flipy.value)
    logcolor = sl.use_reactive(getattr(plotstate, "logcolor").value)
    db_logcolor = sl.lab.use_task(debounce(logcolor.value),
                                  dependencies=[logcolor.value],
                                  prefer_threaded=False)
    if db_logcolor.value == logcolor.value:
        plotstate.logcolor.set(db_logcolor.value)

    with sl.Card(margin=0) as main:
        with Columns([1, 1]):
            with sl.Column():
                if plottype != "heatmap":
                    sl.Switch(label="Log x", value=logx)
                sl.Switch(label="Flip x", value=flipx)
            with sl.Column():
                if plottype != "heatmap":
                    sl.Switch(label="Log y", value=logy)
                if plottype != "histogram":
                    sl.Switch(label="Flip y", value=flipy)
        if plottype != "histogram":
            sl.Switch(label="Color logscale", value=logcolor)
    return main


@sl.component()
def ScatterMenu(plotstate: PlotState, columns):
    """Settings for ScatterPlot

    Args:
        plotstate: plot variables
        columns(list): list of valid columns
    """
    with sl.Column() as main:
        with Card(margin=0):
            with Columns([8, 8, 2], gutters_dense=True):
                SingleAutocomplete(
                    label="Column x",
                    values=[
                        col for col in columns if col != plotstate.y.value
                    ],
                    value=plotstate.x.value,
                    on_value=plotstate.x.set,
                )
                SingleAutocomplete(
                    label="Column y",
                    values=[
                        col for col in columns if col != plotstate.x.value
                    ],
                    value=plotstate.y.value,
                    on_value=plotstate.y.set,
                )
                sl.Button(
                    icon=True,
                    icon_name="mdi-swap-horizontal",
                    on_click=plotstate.swap_axes,
                )
        with Card(margin=0):
            with sl.Column():
                SingleAutocomplete(
                    label="Color",
                    values=columns,
                    value=plotstate.color.value,
                    on_value=plotstate.color.set,
                )
                with sl.Row(gap="2px"):
                    SingleAutocomplete(
                        label="Colorscale",
                        values=list(plotstate.Lookup["colorscales"].keys()),
                        value=plotstate.colorscale.value,
                        on_value=plotstate.colorscale.set,
                    )
    return main


@sl.component()
def HistogramMenu(plotstate: PlotState, columns):
    """Settings for HistogramPlot

    Args:
        plotstate: plot variables
        columns(list): list of valid columns
    """
    nbins = sl.use_reactive(getattr(plotstate, "nbins").value)
    db_nbins = sl.lab.use_task(debounce(nbins.value, 0.05),
                               dependencies=[nbins.value],
                               prefer_threaded=False)
    if db_nbins.value == nbins.value:
        plotstate.nbins.set(db_nbins.value)

    with sl.Column():
        with Card(margin=0):
            with sl.Column():
                SingleAutocomplete(
                    label="Column",
                    values=columns,
                    value=plotstate.x.value,
                    on_value=plotstate.x.set,
                )
        with Card(margin=0):
            sl.SliderInt(
                label="Number of Bins",
                value=nbins,
                step=5,
                min=10,
                max=200,
            )


@sl.component()
def HeatmapMenu(plotstate: PlotState, columns):
    """Settings for HeatmapPlot

    Args:
        plotstate: plot variables
        columns(list): list of valid columns
    """
    nbins = sl.use_reactive(getattr(plotstate, "nbins").value)
    db_nbins = sl.lab.use_task(debounce(nbins.value, 0.05),
                               dependencies=[nbins.value],
                               prefer_threaded=False)
    if db_nbins.value == nbins.value:
        plotstate.nbins.set(db_nbins.value)
    with sl.Column() as main:
        with sl.Card(margin=0):
            with Columns([3, 3, 1], gutters_dense=True):
                SingleAutocomplete(
                    label="Column x",
                    values=[
                        col for col in columns if col != plotstate.y.value
                    ],
                    value=plotstate.x.value,
                    on_value=plotstate.x.set,
                )
                SingleAutocomplete(
                    label="Column y",
                    values=[
                        col for col in columns if col != plotstate.x.value
                    ],
                    value=plotstate.y.value,
                    on_value=plotstate.y.set,
                )
                sl.Button(
                    icon=True,
                    icon_name="mdi-swap-horizontal",
                    on_click=plotstate.swap_axes,
                )
        with sl.Card(margin=0):
            with sl.Column():
                SingleAutocomplete(
                    label="Column to Bin",
                    values=columns,
                    value=plotstate.color.value,
                    on_value=plotstate.color.set,
                    disabled=(str(plotstate.bintype.value) == "count"),
                )
                sl.SliderInt(
                    label="Number of Bins",
                    value=nbins,
                    step=2,
                    min=2,
                    max=240,
                )
                with Columns([1, 1]):
                    with sl.Column():
                        SingleAutocomplete(
                            label="Binning type",
                            values=plotstate.Lookup["bintypes"],
                            value=plotstate.bintype.value,
                            on_value=plotstate.bintype.set,
                        )
                    with sl.Column():
                        SingleAutocomplete(
                            label="Colorscale",
                            values=list(
                                plotstate.Lookup["colorscales"].keys()),
                            value=plotstate.colorscale.value,
                            on_value=plotstate.colorscale.set,
                        )
    return main


@sl.component()
def TableMenu(state: PlotState):
    """Settings menu for Statistics Table view.

    Args:
        state: plot variables

    """
    with sl.Column():
        AutocompleteSelect(
            label="Column",
            value=state.columns.value,
            on_value=state.columns.set,
            values=SubsetState.subsets.value[state.subset.value].columns +
            list(VCData.columns.value.keys()),
            multiple=True,
        )
    return
