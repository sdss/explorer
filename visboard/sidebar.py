"""
Sidebar
"""

import solara as sl

from solara.components.columns import Columns
from solara.components.dataframe import SummaryCard, FilterCard
from solara.components.file_drop import FileDrop

from state import State, PlotState


@sl.component()
def dataset_menu():
    df = State.df.value
    with sl.Row():
        sl.Button(
            "Sample APOGEENET Dataset",
            color="primary",
            text=True,
            outlined=True,
            on_click=State.load_sample,
            disabled=df is not None,
        )
        sl.Button(
            "Clear dataset",
            color="primary",
            text=True,
            outlined=True,
            on_click=State.reset,
        )
    if df is None:
        FileDrop(
            on_file=State.load_from_file,
            on_total_progress=lambda *args: None,
            label="Drag file here",
        )


@sl.component()
def scatter_menu():
    df = State.df.value
    columns = list(map(str, df.columns))
    with Columns([1, 1]):
        sl.Select(
            "Column x",
            values=columns,
            value=PlotState.x,
        )
        sl.Select(
            "Column y",
            values=columns,
            value=PlotState.y,
        )
    with Columns([1, 1]):
        with sl.Column():
            sl.Checkbox(label="Flip x", value=PlotState.flipx)
            sl.Checkbox(label="Log x", value=PlotState.logx)
        with sl.Column():
            sl.Checkbox(label="Flip y", value=PlotState.flipy)
            sl.Checkbox(label="Log y", value=PlotState.logy)
    sl.Select(
        label="Color",
        values=columns,
        value=PlotState.color,
    )


@sl.component()
def statistics_menu():
    df = State.df.value
    columns = list(map(str, df.columns))
    with Columns([1, 1]):
        sl.Select(
            "Column x",
            values=columns,
            value=PlotState.x,
        )
        if State.view.value == "histogram2d":
            sl.Select(
                "Column y",
                values=columns,
                value=PlotState.y,
            )
    with Columns([1, 1]):
        with sl.Column():
            sl.Checkbox(label="Log x", value=PlotState.logx)
            sl.Checkbox(label="Flip x", value=PlotState.flipx)
        with sl.Column():
            sl.Checkbox(label="Log y", value=PlotState.logy)
            if State.view.value == "histogram2d":
                sl.Checkbox(label="Flip y", value=PlotState.flipy)
    sl.SliderInt(
        label="Number of Bins",
        value=PlotState.nbins,
        step=10,
        min=10,
        max=2000,
    )
    if State.view.value == "histogram2d":
        sl.Select(
            label="Binning type",
            values=PlotState.Lookup["bintypes"],
            value=PlotState.bintype,
        )
        if str(PlotState.bintype.value) != "count":
            sl.Select(
                label="Column to Bin",
                values=columns,
                value=PlotState.color,
            )
        sl.Select(
            label="Binning scale",
            values=PlotState.Lookup["binscales"],
            value=PlotState.binscale,
        )
    else:
        sl.Select(
            label="Normalization",
            values=PlotState.Lookup["norms"],
            value=PlotState.norm,
        )


@sl.component()
def plot3d_menu():
    df = State.df.value
    columns = list(map(str, df.columns))
    with Columns([1, 1, 1]):
        sl.Select(
            "Column x",
            values=columns,
            value=PlotState.x,
        )
        sl.Select(
            "Column y",
            values=columns,
            value=PlotState.y,
        )
        sl.Select(
            "Column z",
            values=columns,
            value=PlotState.c,
        )
    with Columns([1, 1, 1]):
        with sl.Column():
            sl.Checkbox(label="Flip x", value=PlotState.flipx)
            sl.Checkbox(label="Log x", value=PlotState.logx)
        with sl.Column():
            sl.Checkbox(label="Flip y", value=PlotState.flipy)
            sl.Checkbox(label="Log y", value=PlotState.logy)
        with sl.Column():
            sl.Checkbox(label="Flip z", value=PlotState.flipz)
            sl.Checkbox(label="Log z", value=PlotState.logz)


@sl.component()
def plot_control_menu():
    df = State.df.value
    if df is not None:
        SummaryCard(df)
        FilterCard(
            df
        )  # TODO: find out why the successful expression menu doesn't work and also why it hella crashes
        if State.view.value == "scatter":
            scatter_menu()
        elif "histogram" in str(State.view.value):
            statistics_menu()
        elif State.view.value == "3d":
            plot3d_menu()
    else:
        sl.Info(
            "No data loaded, click on the sample dataset button to load a sample dataset, or upload a file."
        )


@sl.component()
def sidebar():
    with sl.Sidebar():
        with sl.Card("Controls", margin=0, elevation=0):
            with sl.Column():
                dataset_menu()
                plot_control_menu()
