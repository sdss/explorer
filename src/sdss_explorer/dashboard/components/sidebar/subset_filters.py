"""Holds specific filter components"""

import logging
from typing import cast
from timeit import default_timer as timer

import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement

from ....util.filters import (
    filter_carton_mapper,
    filter_expression,
    filter_flags,
    filter_crossmatch,
    crossmatchList,
    flagList,
)

from ...dataclass import Alert, State, SubsetState, use_subset, VCData
from ..textfield import ExpressionField, InputTextExposed
from .autocomplete import AutocompleteSelect, SingleAutocomplete
from .glossary import Help

__all__ = [
    "ExprEditor", "TargetingFiltersPanel", "PivotTablePanel", "DatasetSelect"
]

logger = logging.getLogger("dashboard")


@sl.component()
def ExprEditor(key: str, invert) -> ValueElement:
    """Expression editor.

    Args:
        key: subset key
        invert (solara.Reactive[bool]): whether to invert or not
    """
    # state for expreditor
    subset = SubsetState.subsets.value[key]
    df = subset.df

    _, set_expfilter = use_subset(id(df), key, "expr", write_only=True)

    expression, set_expression = (
        subset.expression,
        lambda arg: SubsetState.update_subset(key, expression=arg),
    )

    error, set_error = sl.use_state(cast(str, None))

    # Expression Editor thread
    def update_expr():
        """
        Validates if the expression is valid, and returns
        a precise error message for any issues in the expression.
        """
        columns = State.df.value.get_column_names()
        if expression is None or expression == "" or expression == "None":
            set_expfilter(None)
            set_expression("")
            return None
        try:
            exprfilter = filter_expression(df,
                                           columns,
                                           expression,
                                           invert=invert.value)
            set_expfilter(exprfilter)
            return True
        except AssertionError as e:
            # INFO: dont unset filters if assertions fail; tell user and let them try again
            set_error(e)  # saves error msg to state
            return False
        except SyntaxError:
            set_error("modifier at end of sequence with no expression")
            return False

    result: sl.Result[bool] = sl.lab.use_task(
        update_expr,
        dependencies=[df, expression, subset.dataset, invert.value])
    if result.finished:
        if result.value:
            errorFound = False
            message = "Valid expression entered"
        elif result.value is None:
            errorFound = False
            message = "No expression entered. Filter unset."
        else:
            errorFound = True
            message = f"Invalid expression entered: {error}"

    elif result.error:
        errorFound = True
        message = f"Backend failure occurred: {result.error}"
    else:
        # processing
        errorFound = False
        message = None

    def on_append(*args, **kwargs):
        """Append Python-side callback; open expressions help"""
        Help.update("expressions")

    # expression editor
    with sl.Column(gap="0px") as main:
        with sl.Row(justify="center", style={"align-items": "center"}):
            ExpressionField(
                value=expression,
                on_value=set_expression,
                event_on_append=on_append,
                messages=[message],
                error=bool(errorFound),
            )
    return main


@sl.component()
def DatasetSelect(key: str, dataset, set_dataset) -> ValueElement:
    """Select box for pipeline, also sets columns on dataset change.

    Note:
        this component contains subfunctions. See source code.

    Args:
        key: subset key
        dataset (str): dataset value
        set_dataset (Callable[[str],None]): dataset setter function

    """
    subset = SubsetState.subsets.value[key]
    df = State.df.value

    def fetch() -> list:
        """Get complete list of all pipelines for this release/datatype"""
        return df["pipeline"].unique()

    pipelines = sl.use_memo(
        fetch, dependencies=[df, State._release.value, State._datatype.value])

    def update_dataframe():
        """Changes dataframe for given subset"""
        dfg = State.df.value

        # WARNING: this needs to be shallow copied EVERY TIME, else you get
        # weird errors with the vaex chunking because the caches becomes invalidated
        newdf = dfg[dfg[f"(pipeline=='{dataset}')"]].copy().extract()
        newdf = newdf.materialize()  # ensure thing works

        if (dfg is not None) and (State.columns.value is not None):
            SubsetState.update_subset(key,
                                      df=newdf,
                                      columns=State.columns.value[dataset])
        return newdf

    # use memo so this runs and BLOCKS other tasks; this needs to run BEFORE everything else.
    sl.use_memo(update_dataframe, dependencies=[df, dataset])

    def ensure_vc():
        """Ensures all Virtual columns are in and/or removed from current df."""
        sdf = subset.df
        for name, expr in VCData.columns.value.items():
            if name not in sdf.virtual_columns.keys():
                sdf.add_virtual_column(name, expr)

    sl.lab.use_task(ensure_vc, dependencies=[subset.df, VCData.columns.value])

    return SingleAutocomplete(
        label="Dataset",
        values=pipelines,
        value=dataset,
        on_value=set_dataset,
    )


@sl.component()
def FlagSelect(key: str, invert) -> ValueElement:
    """Select box with callback for filters.

    Note:
        this component contains subfunctions. See source code.

    Args:
        key: subset key
        invert (solara.Reactive[bool]): whether to invert the filter

    """
    subset = SubsetState.subsets.value[key]
    df = subset.df
    _, set_flagfilter = use_subset(id(df), key, "flags", write_only=True)
    flags, set_flags = (
        subset.flags,
        lambda arg: SubsetState.update_subset(key, flags=arg),
    )

    def update_flags():
        # TODO: relocate this somewhere better, like into a lookup dataclass or a file
        # get the flag lookup
        if flags:
            concat_filter = filter_flags(df,
                                         flags,
                                         subset.dataset,
                                         invert=invert.value)
        else:
            concat_filter = None

        set_flagfilter(concat_filter)
        return

    sl.lab.use_task(update_flags,
                    dependencies=[flags, subset.dataset, invert.value])

    return AutocompleteSelect(
        label="Quick Flags",
        value=flags,
        on_value=set_flags,
        values=list(flagList.keys()),
        multiple=True,
    )


@sl.component()
def TargetingFiltersPanel(key: str, invert) -> ValueElement:
    """Holds expansion panels for complex filtering

    Note:
        this component contains subfunctions. See source code.

    Args:
        key: subset key
        invert (solara.Reactive[bool]): whether to invert the filter

    """
    mapping = State.mapping.value
    subset = SubsetState.subsets.value[key]
    df = subset.df
    _, set_cmfilter = use_subset(id(df), key, "cartonmapper", write_only=True)
    # handlers for mapper/carton/data/setflags
    mapper, set_mapper = (
        subset.mapper,
        lambda arg: SubsetState.update_subset(key, mapper=arg),
    )
    carton, set_carton = (
        subset.carton,
        lambda arg: SubsetState.update_subset(key, carton=arg),
    )
    combotype = (
        "AND"  # NOTE: remains for functionality as potential state var (in future)
    )

    # Carton Mapper thread
    def update_cm():
        # fail on no mapping
        if mapping is None:
            Alert.update(
                "Mappings file not found! Please contact server admins.",
                color="warning",
            )
            return

        # mapper + cartons
        logger.debug(f"MAPPER: {mapper}")
        logger.debug(f"CARTON: {carton}")
        start = timer()
        cmp_filter = filter_carton_mapper(
            df,
            mapping,
            carton,
            mapper,
            combotype=combotype,
            invert=invert.value,
        )
        # invert if requested
        set_cmfilter(cmp_filter)

        logger.debug(f"CM filter took {timer() - start:.4f} seconds")

        return

    result = sl.lab.use_task(update_cm,
                             dependencies=[df, mapper, carton, invert.value])

    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=[
            rv.Col(
                cols=1,
                children=[
                    "Targeting Filters",
                    sl.ProgressLinear(result.pending),
                ],
            )
        ])
        with rv.ExpansionPanelContent():
            if State.mapping.value is None:
                sl.Warning(
                    dense=True,
                    label=
                    "Mappings file not found! Please contact server admins.",
                )
            else:
                with sl.Column(gap="2px"):
                    AutocompleteSelect(
                        label="Mapper",
                        value=mapper,
                        on_value=set_mapper,
                        values=State.mapping.value["mapper"].unique(),
                    )
                    AutocompleteSelect(
                        label="Carton",
                        value=carton,
                        on_value=set_carton,
                        values=State.mapping.value["alt_name"].unique(),
                    )
                    FlagSelect(key, invert)

    return main


@sl.component()
def CrossmatchPanel(key: str) -> ValueElement:
    """Crossmatch panel"""

    subset = SubsetState.subsets.value[key]
    df = subset.df
    crossmatch, set_crossmatch = (
        subset.crossmatch,
        lambda arg: SubsetState.update_subset(key, crossmatch=arg),
    )
    cmtype, set_cmtype = (
        subset.cmtype,
        lambda arg: SubsetState.update_subset(key, cmtype=arg),
    )

    _, set_filter = use_subset(id(df), key, "crossmatch", write_only=True)

    def update_crossmatch():
        try:
            filter = filter_crossmatch(df, crossmatch, cmtype)
            set_filter(filter)
        except Exception as e:
            Alert.update(f"Crossmatch failed! {e}", color="error")

    result = sl.lab.use_task(update_crossmatch,
                             dependencies=[df, crossmatch, cmtype])
    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=[
            rv.Col(
                cols=1,
                children=[
                    "Crossmatch",
                    sl.ProgressLinear(result.pending),
                ],
            )
        ])
        with rv.ExpansionPanelContent():
            SingleAutocomplete(
                label="ID Type",
                value=cmtype,
                on_value=set_cmtype,
                values=list(crossmatchList.keys()),
            )
            sl.InputTextArea(
                "Enter some identifiers (integer)",
                auto_grow=False,
                value=crossmatch,
                on_value=set_crossmatch,
            )
            with sl.Tooltip("Clear your crossmatch entry."):
                sl.Button("Clear", on_click=lambda: set_crossmatch(""))


@sl.component()
def PivotTablePanel() -> ValueElement:
    """Holds solara PivotTable in expansion panel. Deprecated (maybe implement again in future)"""
    df = State.df.value
    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-table-plus"])
            with rv.CardTitle(children=["Pivot Table"]):
                pass
        with rv.ExpansionPanelContent():
            if not isinstance(df, dict):
                # BUG: says the df is a dictionary when it isnt, no idea why this occurs
                # NOTE: the fix below fixes it, but is weird
                if type(df) != dict:  # noqa
                    sl.PivotTableCard(df, y=["telescope"], x=["release"])
    return main
