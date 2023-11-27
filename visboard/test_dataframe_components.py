import vaex as vx
import solara as sl

from solara.components.dataframe import *


class State:
    df = vx.open("/home/riley/uni/rproj/data/astra-clean.parquet")
    df = df[:500_000]


@sl.component
def Page():
    with sl.Columns([1, 1]):
        SummaryCard(State.df)
        DropdownCard(State.df)
    with sl.Columns([1, 2, 1]):
        HeatmapCard(State.df, "teff", "logg")
        sl.PivotTableCard(State.df, x=["telescope"], y=["gaia_dr3_source_id"])
        HistogramCard(State.df)


@sl.component
def Layout(children):
    route, routes = sl.use_route()
    return sl.AppLayout(children=children)


if __name__ == "__main__":
    Layout(Page())
