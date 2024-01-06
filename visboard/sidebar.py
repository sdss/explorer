import solara as sl

from solara.components.columns import Columns
from solara.components.card import Card
from solara.components.dataframe import SummaryCard, FilterCard
from solara.components.file_drop import FileDrop

from state import State, PlotState
from editor import ExprEditor, SumCard


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
def sky_menu():
    df = State.df.value
    columns = list(map(str, df.columns))
    with Card(margin=0):
        with sl.Row():
            sl.ToggleButtonsSingle(value=PlotState.geo_coords,
                                   values=["ra/dec", "galactic lon/lat"])
        with sl.Row():
            sl.Select(
                label="Color",
                values=columns,
                value=PlotState.color,
            )
            sl.Select(
                label="Colorscale",
                values=PlotState.Lookup["colorscales"],
                value=PlotState.colorscale,
            )
    with Card(margin=0):
        with Columns([1, 1]):
            with sl.Column():
                sl.Switch(label="Flip x", value=PlotState.flipx)
            with sl.Column():
                sl.Switch(label="Flip y", value=PlotState.flipy)


@sl.component()
def scatter_menu():
    df = State.df.value
    columns = list(map(str, df.columns))
    with Card(margin=0):
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
        sl.Select(
            label="Color",
            values=columns,
            value=PlotState.color,
        )
        sl.Select(
            label="Colorscale",
            values=PlotState.Lookup["colorscales"],
            value=PlotState.colorscale,
        )
    with Card(margin=0):
        with Columns([1, 1]):
            with sl.Column():
                sl.Switch(label="Flip x", value=PlotState.flipx)
                sl.Switch(label="Log x", value=PlotState.logx)
            with sl.Column():
                sl.Switch(label="Flip y", value=PlotState.flipy)
                sl.Switch(label="Log y", value=PlotState.logy)


@sl.component()
def statistics_menu():
    df = State.df.value
    columns = list(map(str, df.columns))
    with Card(margin=0):
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
        if State.view.value == "histogram2d":
            sl.Select(
                label="Colorscale",
                values=PlotState.Lookup["colorscales"],
                value=PlotState.colorscale,
            )
    with Card(margin=0):
        if State.view.value == "histogram2d":
            min = 2
            step = 2
        else:
            min = 10
            step = 10
        sl.SliderInt(
            label="Number of Bins",
            value=PlotState.nbins,
            step=step,
            min=min,
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
    with Card(margin=0):
        with Columns([1, 1]):
            with sl.Column():
                sl.Switch(label="Log x", value=PlotState.logx)
                sl.Switch(label="Flip x", value=PlotState.flipx)
            with sl.Column():
                sl.Switch(label="Log y", value=PlotState.logy)
                if State.view.value == "histogram2d":
                    sl.Switch(label="Flip y", value=PlotState.flipy)


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
            sl.Switch(label="Flip x", value=PlotState.flipx)
            sl.Switch(label="Log x", value=PlotState.logx)
        with sl.Column():
            sl.Switch(label="Flip y", value=PlotState.flipy)
            sl.Switch(label="Log y", value=PlotState.logy)
        with sl.Column():
            sl.Switch(label="Flip z", value=PlotState.flipz)
            sl.Switch(label="Log z", value=PlotState.logz)


@sl.component()
def plot_control_menu():
    df = State.df.value

    filter, set_filter = sl.use_cross_filter(id(df), "download")
    if filter:
        dff = df[filter]
    else:
        dff = df

    def get_data():
        dfp = dff.to_pandas_df()
        return dfp.to_csv(index=False)

    if df is not None:
        # summary + expressions
        SumCard()
        ExprEditor()

        # plot controls
        if State.view.value == "scatter":
            scatter_menu()
        elif "histogram" in str(State.view.value):
            statistics_menu()
        elif State.view.value == "skyplot":
            sky_menu()
        sl.FileDownload(
            get_data,
            filename="apogeenet_filtered.csv",
            label="Download table",
        )

        # pivot table
        sl.PivotTableCard(df, x=["telescope"], y=["release"])
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
