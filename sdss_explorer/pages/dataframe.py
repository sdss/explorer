from typing import cast, Optional

import solara as sl
from solara.lab import Menu
import reacton.ipyvuetify as rv

from .state import State


@sl.component
def Loading() -> None:
    sl.Markdown("## Loading")
    sl.Markdown("Loading your embeddings. Enjoy this fun animation for now")
    sl.ProgressLinear(True, color="purple")


@sl.component
def show_table(del_func):
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
        # TODO: add column add/remove functionality
        with rv.Card(class_="grey darken-3",
                     style_="width: 100%; height: 100%"):
            with rv.CardText():
                with sl.Column(classes=["grey darken-3"]):
                    sl.DataTable(
                        dff,
                        items_per_page=10,  # tablestate.height.value,
                        scrollable=True,
                        column_actions=column_actions,
                    )
                    btn = sl.Button(
                        icon_name="mdi-settings",
                        outlined=False,
                        classes=["grey darken-3"],
                    )
                    with Menu(activator=btn, close_on_content_click=False):
                        with sl.Card(margin=0):
                            sl.Button(
                                icon_name="mdi-delete",
                                color="red",
                                block=True,
                                on_click=del_func,
                            )

    else:
        NoDF()


@sl.component
def NoDF() -> None:
    with sl.Columns([1]):
        sl.Info(
            label="No dataset loaded.",
            icon=True,
        )
