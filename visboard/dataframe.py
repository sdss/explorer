import solara as sl

import vaex as vx
from state import State, PlotState


@sl.component
def Loading() -> None:
    sl.Markdown("## Loading")
    sl.Markdown("Loading your embeddings. Enjoy this fun animation for now")
    sl.ProgressLinear(True, color="purple")


@sl.component
def DFView() -> None:
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), name="filter-tableview")
    dff = df
    if df is not None:
        sl.PivotTableCard(df, x=["telescope"], y=["release"])
        if filter:
            dff = df[filter]
        sl.Markdown(f"## Data ({len(dff):,} points)")
        sl.DataFrame(dff)
    else:
        Loading()


@sl.component
def NoDF() -> None:
    sl.Info(
        label=
        "No dataset loaded. Import or select a dataset using the sidebar.",
        icon=True,
    )
