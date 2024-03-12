import solara as sl
from solara import lab
import reacton.ipyvuetify as rv

from state import State
from dataframe import NoDF
from sidebar import sidebar
from grid import ObjectGrid


@sl.component
def Page():
    df = State.df.value
    print(dir(lab.theme))

    # PAGE TITLE
    # TODO: make this adaptive in some cool way
    sl.Title("(NOTPUBLIC) SDSS Visboard")
    with sl.AppBar():
        sl.AppBarTitle(children=[rv.Icon(children=["mdi-orbit"]), " SDSS"])
        sl.Select(
            label="Dataset",
            dense=True,
            values=State.Lookup.datasets,
            value=State.dataset.value,
            on_value=State.load_dataset,
        )
        lab.ThemeToggle()
    # SIDEBAR
    sidebar()
    # MAIN GRID
    if df is not None:
        ObjectGrid()
    else:
        NoDF()
    # TABS
    # with lab.Tabs(grow=True):
    #    with lab.Tab("Table", style=State.style.value):
    #        if df is not None:
    #            DFView()
    #        else:
    #            NoDF()
    #    with lab.Tab("Graph"):
    #        sl.Select(
    #            label="Plot Type",
    #            value=State.view,
    #            values=State.Lookup.views,
    #        )
    #        if df is not None:
    #            if State.view.value in ["scatter"]:
    #                if len(df) > 10000:
    #                    sl.Warning(
    #                        label=
    #                        "Only plotting first 10,000 points. Please use a filter.",
    #                        icon=True,
    #                    )
    #            show_plot(State.view.value)
    #        else:
    #            NoDF()


@sl.component
def Layout(children):
    # route, routes = sl.use_route()

    return sl.AppLayout(sidebar_open=False, children=children, color="purple")


if __name__ == "__main__":
    Layout(Page())
