import solara as sl
import vaex as vx  # noqa

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
        if filter:
            dff = dff[filter]
        dff = dff[[
            "sdss_id",
            "gaia_dr3_source_id",
            "telescope",
            "release",
            PlotState.x.value,
            PlotState.y.value,
            PlotState.color.value,
        ]]
        sl.Markdown(f"## Data ({len(dff):,} points)")
        # sl.DataFrame(dff)
    else:
        Loading()


@sl.component
def NoDF() -> None:
    sl.Info(
        label=
        "No dataset loaded. Import or select a dataset using the sidebar.",
        icon=True,
    )
