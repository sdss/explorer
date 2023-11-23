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


def filtered_df(df: vx.DataFrame):
    dff = df[[
        "sdss_id",
        PlotState.x.value,
        PlotState.y.value,
        PlotState.color.value,
    ]]
    return dff


@sl.component
def DFView() -> None:
    dff = State.df.value
    if PlotState.x.value is not None and PlotState.y.value is not None:
        dff = filtered_df(dff)
        Table(dff)
    else:
        Loading()


@sl.component
def NoDF() -> None:
    sl.Markdown("## No Data Loaded.")
    sl.Markdown("Import or select a dataset using the sidebar.")
