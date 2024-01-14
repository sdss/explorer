import solara as sl

from state import State
from dataframe import NoDF
from sidebar import sidebar
from grid import ObjectGrid


@sl.component
def Page():
    df = State.df.value

    # PAGE TITLE
    title = "[NOT FOR PUBLIC] Visboard"
    sl.Title(title)
    with sl.AppBar():
        sl.AppBarTitle(children=title)
        sl.Button(
            label=None,
            on_click=State.change_theme,
            icon_name="mdi-moon-waning-crescent"
            if State.theme.value else "mdi-white-balance-sunny",
            style=State.style.value,
        )
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
    route, routes = sl.use_route()

    return sl.AppLayout(children=children, toolbar_dark=State.theme.value)


if __name__ == "__main__":
    Layout(Page())
