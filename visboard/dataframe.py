from typing import cast, Optional

import solara as sl
import vaex as vx  # noqa

import reacton.ipyvuetify as rv
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
    column, set_column = sl.use_state(cast(Optional[str], None))
    order, set_order = sl.use_state(cast(bool, None))
    dff = df

    def on_ascend(column):
        set_order(True)
        set_column(column)

    def on_descend(column):
        set_order(False)
        set_column(column)

    column_actions = [
        sl.ColumnAction(icon="mdi-sort-ascending",
                        name="Sort ascending",
                        on_click=on_ascend),
        sl.ColumnAction(icon="mdi-sort-descending",
                        name="Sort descending",
                        on_click=on_descend),
    ]

    if df is not None:
        if filter:
            dff = dff[filter]
        dff = dff[[
            "sdss_id",
            "gaia_dr3_source_id",
            "telescope",
            "release",
            "teff",
            "logg",
            "fe_h",
        ]]
        if column is not None and order is not None:
            dff = dff.sort(dff[column], ascending=order)
        sl.DataTable(dff, column_actions=column_actions)

    else:
        Loading()


@sl.component
def NoDF() -> None:
    sl.Info(
        label=
        "No dataset loaded. Import or select a dataset using the sidebar.",
        icon=True,
    )
