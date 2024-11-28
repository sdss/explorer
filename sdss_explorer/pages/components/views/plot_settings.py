"""Plot settings menus"""

import solara as sl
from solara.components.card import Card
from solara.components.columns import Columns

from sdss_explorer.pages.dataclass import subsetstore

from ...dataclass import State, SubsetState, Subset
from ..sidebar.autocomplete import SingleAutocomplete


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
    subset = SubsetState.subsets.value[plotstate.subset.value]
    columns = subset.df.get_column_names() + subset.virtual_columns
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            len(subset.virtual_columns),
            subset.dataset,
        ],
    )

    name, names = SubsetState.subsets.value.get(
        plotstate.subset.value, Subset(name='temp')).name, [
            ss.name for ss in SubsetState.subsets.value.values()
        ]

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
                    value=plotstate.projection,
                    values=plotstate.Lookup["projections"],
                )
            with sl.Row():
                SingleAutocomplete(
                    label="Color",
                    values=columns,
                    value=plotstate.color,
                )
                SingleAutocomplete(
                    label="Colorscale",
                    values=plotstate.Lookup["colorscales"],
                    value=plotstate.colorscale,
                )
                SingleAutocomplete(
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
    subset = SubsetState.subsets.value[plotstate.subset.value]
    columns = subset.df.get_column_names() + subset.virtual_columns
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            subset.virtual_columns,
            subset.df,
        ],
    )

    name, names = SubsetState.subsets.value.get(
        plotstate.subset.value, Subset(name='temp')).name, [
            ss.name for ss in SubsetState.subsets.value.values()
        ]
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
                        "Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x,
                    )
                    SingleAutocomplete(
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
                    SingleAutocomplete(
                        label="Color",
                        values=columns,
                        value=plotstate.color,
                    )
                    with sl.Row(gap="2px"):
                        SingleAutocomplete(
                            label="Colorscale",
                            values=plotstate.Lookup["colorscales"],
                            value=plotstate.colorscale,
                        )
                        SingleAutocomplete(
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
    print('histogram menu rerender')
    subset = SubsetState.subsets.value[plotstate.subset.value]

    columns = sl.use_memo(subset.df.get_column_names,
                          dependencies=[
                              len(SubsetState.subsets.value),
                              SubsetState.subsets.value, subset,
                              len(subset.virtual_columns), subset.dataset,
                              subset.df
                          ])
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            subset,
            len(subset.virtual_columns),
            subset.dataset,
        ],
    )

    name, names = SubsetState.subsets.value.get(
        plotstate.subset.value, Subset(name='temp')).name, [
            ss.name for ss in SubsetState.subsets.value.values()
        ]

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
            SingleAutocomplete(
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
    subset = SubsetState.subsets.value[plotstate.subset.value]
    columns = subset.df.get_column_names() + subset.virtual_columns
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            subset.virtual_columns,
            subset.df,
        ],
    )

    name, names = SubsetState.subsets.value.get(
        plotstate.subset.value, Subset(name='temp')).name, [
            ss.name for ss in SubsetState.subsets.value.values()
        ]

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
                        "Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x,
                    )
                with sl.Column():
                    SingleAutocomplete(
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
            SingleAutocomplete(
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
            SingleAutocomplete(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype,
            )
            SingleAutocomplete(label="Column to Bin",
                               values=columns,
                               value=plotstate.color,
                               disabled=(str(
                                   plotstate.bintype.value) == "count"))
            SingleAutocomplete(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale,
            )


@sl.component()
def DeltaHeatmapMenu(plotstate):
    """Settings for DeltaHeatmapPlot"""
    subset = SubsetState.subsets.value[plotstate.subset.value]
    columns = subset.df.get_column_names() + subset.virtual_columns
    sl.use_thread(
        plotstate.reset_values,
        dependencies=[
            len(SubsetState.subsets.value),
            SubsetState.subsets.value,
            subset.virtual_columns,
            subset.df,
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
                        "Column x",
                        values=[
                            col for col in columns if col != plotstate.y.value
                        ],
                        value=plotstate.x,
                    )
                with sl.Column():
                    SingleAutocomplete(
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
            SingleAutocomplete(
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
            SingleAutocomplete(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype,
            )
            if str(plotstate.bintype.value) != "count":
                SingleAutocomplete(
                    label="Column to Bin",
                    values=columns,
                    value=plotstate.color,
                )
            SingleAutocomplete(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale,
            )
