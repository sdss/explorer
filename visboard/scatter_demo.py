import solara as sl
import solara.lab as lab
from solara.components.columns import Columns
from solara.components.file_drop import FileDrop

from state import State, PlotState
from dataframe import DFView, NoDF
from plots import show_plot


@sl.component
def Page():
    df = State.df.value

    # SIDEBAR
    with sl.Sidebar():
        with sl.Card("Controls", margin=0, elevation=0):
            with sl.Column():
                with sl.Row():
                    sl.Button(
                        "Sample dataset",
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
                FileDrop(
                    on_file=State.load_from_file,
                    on_total_progress=lambda *args: None,
                    label="Drag file here",
                )

                if df is not None:
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
                    sl.Checkbox(label="Log x", value=PlotState.logx)
                    sl.Checkbox(label="Log y", value=PlotState.logy)
                    sl.Checkbox(label="Flip x", value=PlotState.flipx)
                    sl.Checkbox(label="Flip y", value=PlotState.flipy)
                    sl.Select(
                        "Color",
                        values=columns,
                        value=PlotState.color,
                    )
                    sl.SliderInt(
                        label="Number of Bins",
                        value=PlotState.nbins,
                        step=10,
                        min=10,
                        max=1000,
                    )
                    sl.Select(
                        label="Normalization",
                        values=PlotState.norms,
                        value=PlotState.norm,
                    )
                else:
                    sl.Info(
                        "No data loaded, click on the sample dataset button to load a sample dataset, or upload a file."
                    )

    # TABS
    with lab.Tabs(grow=True):
        with lab.Tab("Table"):
            if df is not None:
                DFView()
            else:
                NoDF()
        with lab.Tab("Histogram"):
            show_plot("histogram")
        with lab.Tab("Histogram 2D"):
            show_plot("histogram2d")
        with lab.Tab("Scatter"):
            show_plot("scatter")


@sl.component
def Layout(children):
    route, routes = sl.use_route()
    return sl.AppLayout(children=children)


if __name__ == "__main__":
    Layout(Page())
