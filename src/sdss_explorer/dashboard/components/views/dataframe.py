"""Functions for processing dataframes for the Table views."""

import dataclasses
import math
import os
from dataclasses import replace
from typing import Any, Callable, List, Optional, cast, Union

import ipyvuetify as v
import ipywidgets
import solara as sl
import solara.lab
import traitlets
from solara.components.datatable import CellAction, ColumnAction

# NOTE: these 'df' functions disable reactive bindings on DF and pre-compile the
# component. they also cant be imported from the solara namespace


def df_type(df):
    return df.__class__.__module__.split(".")[0]


def df_len(df) -> int:
    """Return the number of rows in a dataframe."""
    return len(df)


def df_columns(df) -> List[str]:
    """Return a list of column names from a dataframe."""
    if df_type(df) == "vaex":
        return df.get_column_names()
    elif df_type(df) == "pandas":
        return df.columns.tolist()
    elif df_type(df) == "polars":
        return df.columns
    else:
        raise TypeError(f"{type(df)} not supported")


def df_row_names(df) -> List[Union[int, str]]:
    """Return a list of row names from a dataframe."""
    if df_type(df) == "vaex" or df_type(df) == "polars":
        return list(range(df_len(df)))
    elif df_type(df) == "pandas":
        return df.index.tolist()
    else:
        raise TypeError(f"{type(df)} not supported")


def df_slice(df, start: int, stop: int):
    """Return a subset of rows from a dataframe."""
    if df_type(df) == "pandas":
        return df.iloc[start:stop]
    else:
        return df[start:stop]


def df_records(df) -> List[dict]:
    """A list of records from a dataframe."""
    if df_type(df) == "pandas":
        return df.to_dict("records")
    elif df_type(df) == "polars":
        return df.to_dicts()
    elif df_type(df) == "vaex":
        return df.to_records()
    else:
        raise TypeError(f"{type(df)} not supported")


def df_unique(df, column, limit=None):
    if df_type(df) == "vaex":
        return df.unique(column,
                         limit=limit + 1 if limit else None,
                         limit_raise=False)
    if df_type(df) == "pandas":
        x = df[column].unique()  # .to_numpy()
        return x[:limit]
    else:
        raise TypeError(f"{type(df)} not supported")


@sl.component()
def Loading() -> None:
    sl.Markdown("## Loading")
    sl.Markdown("Loading your embeddings. Enjoy this fun animation for now")
    sl.ProgressLinear(True, color="purple")


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
                                 "../../../vue/datatable.vue")

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
    label = traitlets.Any("").tag(sync=True)
    hide_footer = traitlets.Bool(False).tag(sync=True)
    footer_props = traitlets.Dict({}).tag(sync=True)

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


@sl.component()
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

    columns = df.columns.tolist()
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
        hide_footer=True,
        headers=headers,
        headers_selections=[],
        options=options,
        label="Stat",
        items_per_page=items_per_page,
        footer_props={},
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
def TargetsDataTable(
    df,
    columns,
    page=0,
    items_per_page=20,
    format=None,
    column_actions: List[ColumnAction] = [],
    cell_actions: List[CellAction] = [],
    scrollable=False,
    on_column_header_hover: Optional[Callable[[Optional[str]], None]] = None,
    column_header_info: Optional[sl.Element] = None,
):
    total_length = df_len(df)
    options = {
        "descending": False,
        "page": page + 1,
        "itemsPerPage": items_per_page,
        "sortBy": [],
        "totalItems": total_length,
    }
    options, set_options = solara.use_state(options, key="options")
    format = format or format_default
    # frontend does 1 base, we use 0 based
    page = options["page"] - 1
    items_per_page = options["itemsPerPage"]
    i1 = page * items_per_page
    i2 = min(total_length, (page + 1) * items_per_page)

    rows = df_row_names(df)
    items = []
    dfs = df_slice(df, i1, i2)
    records = df_records(dfs)

    for i in range(i2 - i1):
        item = {
            "__row__": format(dfs, columns, i + 1, rows[i + i1])
        }  # special key for the row number
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
        footer_props={
            "items-per-page-options": [],
            "items-per-page-text": ""
        },
        rows_per_page_text="",
        rows_per_page_items=[10],
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


@sl.component()
def NoDF() -> None:
    with sl.Columns([1]):
        sl.Info(
            label=
            "No dataset loaded. Please inform server admins to set EXPLORER_DATAPATH envvar and ensure app has read-access to data files.",
            icon=True,
        )
