import solara as sl

import vaex as vx
from state import State, PlotState


@sl.component
def Loading() -> None:
    sl.Markdown("## Loading")
    sl.Markdown("Loading your embeddings. Enjoy this fun animation for now")
    sl.ProgressLinear(True, color="purple")


@sl.component
def Table(df: vx.DataFrame) -> None:
    sl.Markdown(f"## Data ({len(df):,} points)")
    sl.DataFrame(df)


@sl.component
def DFView() -> None:
    df = State.df.value
    filter, use_filter = sl.use_cross_filter(id(df), "filter-viewing")
    dff = df
    if filter:
        dff = dff[filter]
    if PlotState.x.value is not None and PlotState.y.value is not None:
        sl.Markdown(f"## Data ({len(df):,} points)")
        sl.PivotTableCard(dff)
    else:
        Loading()


@sl.component
def NoDF() -> None:
    sl.Info(
        label=
        "No dataset loaded. Import or select a dataset using the sidebar.",
        icon=True,
    )
