import dataclasses
import math
import os
from dataclasses import replace
from typing import Any, Callable, List, Optional, cast

import ipyvuetify as v
import ipywidgets
import pandas as pd
import reacton.ipyvuetify as rv
import solara
import solara as sl
import solara.hooks.dataframe
import solara.lab
import traitlets
from solara.components.datatable import CellAction, ColumnAction
from solara.lab import Menu, Task, use_task
from solara.lab.hooks.dataframe import use_df_column_names

from .state import State
from .subsets import use_subset


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


def format_default(df, column, row_index, value):
    """Format strings properly"""
    if isinstance(value, float) and math.isnan(value):
        return "NaN"
    return str(value)


def _ensure_dict(d):
    if dataclasses.is_dataclass(d):
        return dataclasses.asdict(d)
    return d


def _drop_keys_from_list_of_mappings(drop):
    """Generates function to drop key from mapppings"""

    def closure(list_of_dicts, widget):
        return [{
            k: v
            for k, v in _ensure_dict(d).items() if k not in drop
        } for d in list_of_dicts]

    return closure


class DataTableWidget(v.VuetifyTemplate):
    template_file = os.path.join(os.path.dirname(__file__),
                                 "../vue/datatable.vue")

    total_length = traitlets.CInt().tag(sync=True)
    checked = traitlets.List(cast(List[Any], [])).tag(
        sync=True)  # indices of which rows are selected
    column_actions = traitlets.List(
        trait=traitlets.Instance(ColumnAction), default_value=[]).tag(
            sync=True, to_json=_drop_keys_from_list_of_mappings(["on_click"]))
    _column_actions_callbacks = traitlets.List(trait=traitlets.Callable(),
                                               default_value=[])
    cell_actions = traitlets.List(trait=traitlets.Instance(CellAction),
                                  default_value=[]).tag(
                                      sync=True,
                                      to_json=_drop_keys_from_list_of_mappings(
                                          ["on_click"]))
    _cell_actions_callbacks = traitlets.List(trait=traitlets.Callable(),
                                             default_value=[])
    items = traitlets.Any().tag(sync=True)  # the data, a list of dict
    headers = traitlets.Any().tag(sync=True)
    headers_selections = traitlets.Any().tag(sync=True)
    options = traitlets.Any().tag(sync=True)
    items_per_page = traitlets.CInt(11).tag(sync=True)
    selections = traitlets.Any([]).tag(sync=True)
    selection_colors = traitlets.Any([]).tag(sync=True)
    selection_enabled = traitlets.Bool(True).tag(sync=True)
    highlighted = traitlets.Int(None, allow_none=True).tag(sync=True)
    scrollable = traitlets.Bool(False).tag(sync=True)

    # for use with scrollable, when used in the default UI
    height = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    hidden_components = traitlets.List(cast(List[Any], [])).tag(sync=False)
    column_header_hover = traitlets.Unicode(allow_none=True).tag(sync=True)
    column_header_widget = traitlets.Any(allow_none=True).tag(
        sync=True, **ipywidgets.widget_serialization)

    def vue_on_column_action(self, data):
        header_value, action_index = data
        on_click = self._column_actions_callbacks[action_index]
        if on_click:
            on_click(header_value)

    def vue_on_cell_action(self, data):
        row, header_value, action_index = data
        on_click = self._cell_actions_callbacks[action_index]
        if on_click:
            on_click(header_value, row)


@sl.component
def ModdedDataTable(
    df,
    page=0,
    items_per_page=20,
    format=None,
    column_actions: List[ColumnAction] = [],
    cell_actions: List[CellAction] = [],
    scrollable=False,
    on_column_header_hover: Optional[Callable[[Optional[str]], None]] = None,
    column_header_info: Optional[sl.Element] = None,
):
    total_length = len(df)
    options = {}
    options, set_options = sl.use_state(options, key="options")
    format = format or format_default
    # frontend does 1 base, we use 0 based
    page = 0
    items_per_page = 7
    i1 = page * items_per_page
    i2 = min(total_length, (page + 1) * items_per_page)

    columns = use_df_column_names(df)

    items = []
    dfs = df.iloc[i1:i2]
    records = df.to_dict("records")
    for i in range(i2 - i1):
        item = {"__row__": dfs.index[i]}  # special key for the row number
        for column in columns:
            item[column] = format(dfs, column, i + i1, records[i][column])
        items.append(item)

    headers = [{
        "text": name,
        "value": name,
        "sortable": False
    } for name in columns]
    column_actions_callbacks = [k.on_click for k in column_actions]
    cell_actions_callbacks = [k.on_click for k in cell_actions]
    column_actions = [replace(k, on_click=None) for k in column_actions]
    cell_actions = [replace(k, on_click=None) for k in cell_actions]

    return DataTableWidget.element(
        total_length=total_length,
        items=items,
        headers=headers,
        headers_selections=[],
        options=options,
        items_per_page=items_per_page,
        selections=[],
        selection_colors=[],
        selection_enabled=False,
        highlighted=None,
        scrollable=scrollable,
        on_options=set_options,
        column_actions=column_actions,
        cell_actions=cell_actions,
        _column_actions_callbacks=column_actions_callbacks,
        _cell_actions_callbacks=cell_actions_callbacks,
        on_column_header_hover=on_column_header_hover,
        column_header_widget=column_header_info,
    )


@sl.component
def DescribeDF(del_func):
    """Statistics description view for the dataset."""
    df = State.df.value
    subset = sl.use_reactive(State.subsets.value[-1])  # inits with last subset
    filter, set_filter = use_subset(id(df), subset, name="statsview")
    columns, set_columns = sl.use_state(["teff", "logg", "fe_h"])

    if filter:
        dff = df[filter]
    else:
        dff = df

    # the summary table is its own DF (for render purposes)
    # NOTE: worker process concerns if this takes more than 10MB.

    def generate_describe() -> pd.DataFrame:
        """Generates the description table only on column/filter updates"""
        # INFO: vaex returns a pandas df.describe()
        return dff[columns].describe(strings=False)

    result: Task[pd.DataFrame] = use_task(
        generate_describe, dependencies=[filter, columns,
                                         len(columns)])

    def remove_column(name):
        """Removes column from column list"""
        # perform removal via slice (cannot modify inplace)
        # TODO: check if slicing is actually necessary

        q = None
        for i, col in enumerate(columns):
            if col == name:
                q = i
                break

        set_columns(columns[:q] + columns[q + 1:])

    column_actions = [
        # TODO: a more complex action in here?
        sl.ColumnAction(icon="mdi-delete",
                        name="Remove column",
                        on_click=remove_column),
    ]

    with rv.Card(class_="grey darken-3",
                 style_="width: 100%; height: 100%") as main:
        with rv.CardText():
            with sl.Column(classes=["grey darken-3"]):
                sl.ProgressLinear(result.pending)
                if ~result.not_called and result.latest is not None:
                    ModdedDataTable(
                        result.latest,
                        items_per_page=7,
                        column_actions=column_actions,
                    )
                else:
                    NoDF()
                btn = sl.Button(
                    icon_name="mdi-settings",
                    outlined=False,
                    classes=["grey darken-3"],
                )
                # settings menu
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        with sl.Columns([2, 1]):
                            sl.SelectMultiple(
                                label="Columns",
                                values=columns,
                                all_values=State.columns.value,
                                on_value=set_columns,
                            )
                            sl.Select(
                                label="Subset",
                                values=State.subsets.value,
                                value=subset,
                            )
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=del_func,
                        )
    return main


@sl.component
def NoDF() -> None:
    with sl.Columns([1]):
        sl.Info(
            label="No dataset loaded.",
            icon=True,
        )
