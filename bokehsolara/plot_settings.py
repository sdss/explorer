"""Plot settings menus"""

from reacton.ipyvuetify import ValueElement
import solara as sl
import asyncio
from solara.components.card import Card
from solara.components.columns import Columns

from state import df, PlotState
# from ...dataclass import SubsetState, Subset, VCData
# from ..sidebar.autocomplete import SingleAutocomplete, AutocompleteSelect

SingleAutocomplete = sl.Select


def show_settings(type, state):
    """Wrapper to case switch logic for menus"""
    # subset = SubsetState.subsets.value.get(state.subset.value,
    #                                       Subset(name="temp"))
    # columns = list(VCData.columns.value.keys()) + subset.columns
    # sl.lab.use_task(
    #    state.reset_values,
    #    dependencies=[
    #        len(SubsetState.subsets.value),
    #        SubsetState.subsets.value,
    #        VCData.columns.value,
    #        subset.dataset,
    #    ],
    # )
    # name, names = (
    #    subset.name,
    #    [ss.name for ss in SubsetState.subsets.value.values()],
    # )
    columns = df.get_column_names()
    name = "a"
    names = ["a"]

    # specific plot controls
    with sl.Card():
        SingleAutocomplete(
            label="Subset",
            values=names,
            value=name,
            # on_value=plotstate.update_subset,
        )
        with sl.Columns([1, 1]):
            if type == "scatter":
                ScatterMenu(state, columns)
            elif type == "histogram":
                HistogramMenu(state, columns)
            elif type == "heatmap":
                HeatmapMenu(state, columns)
            elif type == "skyplot":
                SkymapMenu(state, columns)
            elif type == "stats":
                StatisticsTableMenu(state, columns)
            if type != "stats":
                CommonSettings(state)
    return


def debounce(value, sleep: float = 0.1):
    """Generates a debouncer function"""
    print("generating debouncer")

    async def debouncer():
        print("debouncing")
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
def SkymapMenu(plotstate, columns):
    """Settings for SkymapPlot"""

    with sl.Column():
        with Card(margin=0):
            with sl.Column():
                sl.ToggleButtonsSingle(value=plotstate.geo_coords,
                                       values=["celestial", "galactic"])
                SingleAutocomplete(
                    label="Projection",
                    value=plotstate.projection.value,
                    on_value=plotstate.projection.set,
                    values=plotstate.Lookup["projections"],
                )
        with Card(margin=0):
            with sl.Column():
                SingleAutocomplete(
                    label="Color",
                    values=columns,
                    value=plotstate.color.value,
                    on_value=plotstate.color,
                )
            with sl.Row():
                SingleAutocomplete(
                    label="Colorscale",
                    values=plotstate.Lookup["colorscales"],
                    value=plotstate.colorscale.value,
                    on_value=plotstate.colorscale.set,
                )
                SingleAutocomplete(
                    label="Color log",
                    values=plotstate.Lookup["binscales"],
                    value=plotstate.logcolor.value,
                    on_value=plotstate.logcolor.set,
                    # allow_none=True,
                )


@sl.component()
def ScatterMenu(plotstate, columns):
    """Settings for ScatterPlot"""
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
                        values=plotstate.Lookup["colorscales"],
                        value=plotstate.colorscale.value,
                        on_value=plotstate.colorscale.set,
                    )
    return main


@sl.component()
def HistogramMenu(plotstate, columns):
    """Settings for HistogramPlot"""
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
                step=10,
                min=10,
                max=1000,
            )
            SingleAutocomplete(
                label="Bintype",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype.value,
                on_value=plotstate.bintype.set,
            )


@sl.component()
def HeatmapMenu(plotstate, columns):
    """Settings for HeatmapPlot"""
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
                    max=250,
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
                            values=plotstate.Lookup["colorscales"],
                            value=plotstate.colorscale.value,
                            on_value=plotstate.colorscale.set,
                        )
    return main


@sl.component()
def StatisticsTableMenu(state):
    """Settings menu for Statistics Table view."""
    with sl.Columns([2, 1]):
        AutocompleteSelect(
            label="Column",
            value=state.columns.value,
            on_value=state.columns.set,
            values=SubsetState.subsets.value[state.subset.value].columns +
            list(VCData.columns.value.keys()),
            multiple=True,
        )
    return


@sl.component()
def DeltaHeatmapMenu(plotstate):
    """Settings for DeltaHeatmapPlot"""
    columns = (list(VCData.columns.value.keys()) +
               SubsetState.subsets.value[plotstate.subset.value].columns)
    sl.lab.use_task(
        plotstate.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
        ],
    )
    name_a = SubsetState.subsets.value[plotstate.subset.value].name
    name_b = SubsetState.subsets.value[plotstate.subset_b.value].name
    names = SubsetState.subsets.value.keys()

    with Card(margin=0):
        with sl.Columns([3, 3, 1]):
            SingleAutocomplete(
                label="Subset 1",
                values=[n for n in names if n != name_b],
                value=name_a,
                on_value=plotstate.update_subset,
            )
            SingleAutocomplete(
                label="Subset 2",
                values=[n for n in names if n != name_a],
                value=name_b,
                on_value=lambda *args: plotstate.update_subset(*args, b=True),
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
                    SingleAutocomplete(
                        label="Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x.value,
                        on_value=plotstate.x.set,
                    )
                with sl.Column():
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
            SingleAutocomplete(
                label="Colorscale",
                values=plotstate.Lookup["colorscales"],
                value=plotstate.colorscale.value,
                on_value=plotstate.colorscale.set,
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
            SingleAutocomplete(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype.value,
                on_value=plotstate.bintype.set,
            )
            if str(plotstate.bintype.value) != "count":
                SingleAutocomplete(
                    label="Column to Bin",
                    values=columns,
                    value=plotstate.color.value,
                    on_value=plotstate.color.set,
                )
            SingleAutocomplete(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale.value,
                on_value=plotstate.binscale.set,
                # allow_none=True,
            )
