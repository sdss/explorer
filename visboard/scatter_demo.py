import solara as sl
import solara.lab as lab

from state import State, PlotState
from dataframe import DFView, NoDF
from plots import show_plot
from sidebar import sidebar


@sl.component
def Page():
    df = State.df.value

    # SIDEBAR
    sidebar()
    # TABS
    with lab.Tabs(grow=True):
        with lab.Tab("Table"):
            if df is not None:
                DFView()
            else:
                NoDF()
        with lab.Tab("Graph"):
            sl.Select(
                label="Plot Type",
                value=State.view,
                values=["histogram", "histogram2d", "scatter"],
            )
            if df is not None:
                if State.view.value in ["scatter"]:
                    if len(df) > 10000:
                        sl.Warning(
                            label=
                            "Only plotting first 10,000 points. Please use a filter.",
                            icon=True,
                        )
                show_plot(State.view.value)
            else:
                NoDF()


@sl.component
def Layout(children):
    route, routes = sl.use_route()
    return sl.AppLayout(children=children)


if __name__ == "__main__":
    Layout(Page())
