import solara as sl

from solara.components.columns import Columns
from solara.components.card import Card
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
def control_menu():
    df = State.df.value

    filter, set_filter = sl.use_cross_filter(id(df), "download")
    if filter:
        dff = df[filter]
    else:
        dff = df

    def get_data():
        dfp = dff.to_pandas()
        return dfp.to_csv(index=False)

    if df is not None:
        # summary + expressions
        SumCard()
        ExprEditor()

        # pivot table
        sl.PivotTableCard(df, x=["telescope"], y=["release"])

        with sl.Row(style={"align-items": "center"}):
            sl.FileDownload(
                get_data,
                filename="apogeenet_filtered.csv",
                label="Download table",
            )
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
                control_menu()
