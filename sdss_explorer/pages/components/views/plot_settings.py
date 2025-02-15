"""Plot settings menus"""

import solara as sl
from solara.components.card import Card
from solara.components.columns import Columns

from sdss_explorer.pages.dataclass.vcdata import VCData

from ...dataclass import SubsetState, Subset
from ..sidebar.autocomplete import SingleAutocomplete, AutocompleteSelect


def show_settings(type, state):
    """Wrapper to case switch logic for menus"""
    subset = SubsetState.subsets.value.get(state.subset.value,
                                           Subset(name="temp"))
    columns = list(VCData.columns.value.keys()) + subset.columns
    sl.lab.use_task(
        state.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            VCData.columns.value,
            subset.dataset,
        ],
    )
    name, names = (
        subset.name,
        [ss.name for ss in SubsetState.subsets.value.values()],
    )

    # specific plot controls
    if type == "scatter":
        return ScatterMenu(state, columns, name, names)
    elif type == "histogram":
        return HistogramMenu(state, columns, name, names)
    elif type == "heatmap":
        return HeatmapMenu(state, columns, name, names)
    elif type == "skyplot":
        return SkymapMenu(state, columns, name, names)
    elif type == "delta2d":
        return None  # DeltaHeatmapMenu(state, columns, name, names)
    elif type == "stats":
        return StatisticsTableMenu(state, columns, name, names)


@sl.component()
def SkymapMenu(plotstate, columns, name, names):
    """Settings for SkymapPlot"""

    with sl.Columns([1, 1]):
        with Card(margin=0):
            SingleAutocomplete(
                label="Subset",
                values=names,
                value=name,
                on_value=plotstate.update_subset,
            )
            with sl.Column():
                sl.ToggleButtonsSingle(value=plotstate.geo_coords,
                                       values=["celestial", "galactic"])
                SingleAutocomplete(
                    label="Projection",
                    value=plotstate.projection.value,
                    on_value=plotstate.projection.set,
                    values=plotstate.Lookup["projections"],
                )
            with sl.Row():
                SingleAutocomplete(
                    label="Color",
                    values=columns,
                    value=plotstate.color.value,
                    on_value=plotstate.color,
                )
                SingleAutocomplete(
                    label="Colorscale",
                    values=plotstate.Lookup["colorscales"],
                    value=plotstate.colorscale.value,
                    on_value=plotstate.colorscale.set,
                )
                SingleAutocomplete(
                    label="Color log",
                    values=plotstate.Lookup["binscales"],
                    value=plotstate.colorlog.value,
                    on_value=plotstate.colorlog.set,
                    allow_none=True,
                )
        with Card(margin=0):
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)


@sl.component()
def ScatterMenu(plotstate, columns, name, names):
    """Settings for ScatterPlot"""
    with sl.Card():
        SingleAutocomplete(
            label="Subset",
            values=names,
            value=name,
            on_value=plotstate.update_subset,
        )
        with sl.Columns([1, 1]):
            with sl.Column():
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
                        SingleAutocomplete(
                            label="Color log",
                            values=plotstate.Lookup["binscales"],
                            value=plotstate.colorlog.value,
                            on_value=plotstate.colorlog.set,
                            allow_none=True,
                        )
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                    sl.Switch(label="Log x", value=plotstate.logx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                    sl.Switch(label="Log y", value=plotstate.logy)


@sl.component()
def HistogramMenu(plotstate, columns, name, names):
    """Settings for HistogramPlot"""

    with sl.Card():
        SingleAutocomplete(
            label="Subset",
            values=names,
            value=name,
            on_value=plotstate.update_subset,
        )
    with sl.Columns([1, 1]):
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
                value=plotstate.nbins,
                step=10,
                min=10,
                max=1e3,
            )
            SingleAutocomplete(
                label="Bintype",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype.value,
                on_value=plotstate.bintype.set,
            )
    with Card(margin=0):
        with sl.Columns([1, 1, 1], style={"align-items": "center"}):
            sl.Switch(label="Log x", value=plotstate.logx)
            sl.Switch(label="Flip x", value=plotstate.flipx)
            sl.Switch(label="Log y", value=plotstate.logy)


@sl.component()
def HeatmapMenu(plotstate, columns, name, names):
    """Settings for HeatmapPlot"""

    with sl.Columns([1, 1]):
        with sl.Card():
            SingleAutocomplete(
                label="Subset",
                values=names,
                value=name,
                on_value=plotstate.update_subset,
            )
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
                max=250,
            )
            SingleAutocomplete(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype.value,
                on_value=plotstate.bintype.set,
            )
            SingleAutocomplete(
                label="Column to Bin",
                values=columns,
                value=plotstate.color.value,
                on_value=plotstate.color.set,
                disabled=(str(plotstate.bintype.value) == "count"),
            )
            SingleAutocomplete(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale.value,
                on_value=plotstate.binscale.set,
                allow_none=True,
            )


@sl.component()
def StatisticsTableMenu(state, columns, name, names):
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

        SingleAutocomplete(
            label="Subset",
            values=names,
            value=name,
            on_value=state.update_subset,
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
                allow_none=True,
            )
