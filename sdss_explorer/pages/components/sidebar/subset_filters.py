"""Holds specific filter components"""

import operator
import logging
import re
from functools import reduce
from typing import cast
from timeit import default_timer as timer

import numpy as np
import vaex as vx
import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement

from ...dataclass import Alert, State, SubsetState, use_subset, VCData
from ..textfield import InputTextExposed
from .autocomplete import AutocompleteSelect, SingleAutocomplete
from .glossary import Help

__all__ = [
    "ExprEditor", "TargetingFiltersPanel", "PivotTablePanel", "DatasetSelect"
]

logger = logging.getLogger("sdss_explorer")

operator_map = {"AND": operator.and_, "OR": operator.or_, "XOR": operator.xor}

flagList = {
    # TODO: more quick flags based on scientist input
    "sdss5 only": "release=='sdss5'",
    "snr > 50": "snr>=50",
    "purely non-flagged": "result_flags==0",
    #'no apo 1m': "telescope!='apo1m'", # WARNING: this one doesn't work for some reason, maybe it's not string; haven't checked
    "no bad flags": "flag_bad==0",
    "gmag < 17": "g_mag<=17",
}


@sl.component()
def ExprEditor(key: str, invert) -> ValueElement:
    """Expression editor."""
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
        try:
            if expression is None or expression == "" or expression == "None":
                set_expfilter(None)
                set_expression("")
                return None
            # first, remove all spaces
            expr = expression.replace(" ", "")
            num_regex = r"^-?[0-9]+(?:\.[0-9]+)?(?:e-?\d+)?$"

            # get expression in parts, saving split via () regex
            subexpressions = re.split(r"(&|\||\)|\()", expr)
            n = 1
            for i, expr in enumerate(subexpressions):
                # saved regex info -> skip w/o enumerating
                if expr in ["", "&", "(", ")", "|"]:
                    continue

                parts = re.split(r"(>=|<=|<|>|==|!=)", expr)
                if len(parts) == 1:
                    assert False, f"expression {n} is invalid: no comparator"
                elif len(parts) == 5:
                    # first, check that parts 2 & 4 are lt or lte comparators
                    assert (
                        re.fullmatch(r"<=|<", parts[1]) is not None
                        and re.fullmatch(r"<=|<", parts[3]) is not None
                    ), f"expression {n} is invalid: not a proper 3-part inequality (a < col <= b)"

                    # check middle
                    assert (
                        parts[2] in columns
                    ), f"expression {n} is invalid: must be comparing a data column (a < col <= b)"

                    # check a and b & if a < b
                    assert (
                        re.match(num_regex, parts[0]) is not None
                    ), f"expression {n} is invalid: must be numeric for numerical data column"
                    assert (
                        float(parts[0]) < float(parts[-1])
                    ), f"expression {n} is invalid: invalid inequality (a > b for a < col < b)"

                    # change the expression to valid format
                    subexpressions[i] = (
                        f"(({parts[0]}{parts[1]}{parts[2]})&({parts[2]}{parts[3]}{parts[4]}))"
                    )

                elif len(parts) == 3:
                    check = (parts[0] in columns, parts[2] in columns)
                    if np.any(check):
                        if check[0]:
                            col = parts[0]
                            num = parts[2]
                        elif check[1]:
                            col = parts[2]
                            num = parts[0]
                        dtype = str(df[col].dtype)
                        if "float" in dtype or "int" in dtype:
                            assert (
                                re.match(num_regex, num) is not None
                            ), f"expression {n} is invalid: must be numeric for numerical data column"
                    else:
                        assert (
                            False
                        ), f"expression {n} is invalid: one part must be column"
                    assert (
                        re.match(r">=|<=|<|>|==|!=", parts[1]) is not None
                    ), f"expression {n} is invalid: middle is not comparator"

                    # change the expression in subexpression
                    subexpressions[i] = "(" + expr + ")"
                else:
                    assert False, f"expression {n} is invalid: too many comparators"

                # enumerate the expr counter
                n = n + 1

            # create expression as str
            expr = "(" + "".join(subexpressions) + ")"

            # set filter corresponding to inverts & exit
            if invert.value:
                set_expfilter(~df[expr])
            else:
                set_expfilter(df[expr])
            return True

        except AssertionError as e:
            # INFO: it's probably better NOT to unset filters if assertions fail.
            # set_filter(None)
            set_error(e)  # saves error msg to state
            return False
        except SyntaxError:
            set_error("modifier at end of sequence with no expression")
            return False

    result: sl.Result[bool] = sl.lab.use_task(
        update_expr, dependencies=[expression, subset.dataset, invert.value])
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

    def add_effect(el: sl.Element):

        def add_append_handler():

            def on_click(widget, event, data):
                Help.update("expressions")

            widget = sl.get_widget(el)
            widget.on_event("click:append", on_click)

            def cleanup():
                widget.on_event("click:append", on_click, remove=True)

            return cleanup

        def add_clear_handler():

            def on_click(widget, event, data):
                set_expression("")
                widget.v_model = ""

            widget = sl.get_widget(el)
            widget.on_event("click:clear", on_click)

            def cleanup():
                widget.on_event("click:clear", on_click, remove=True)

            return cleanup

        sl.use_effect(add_append_handler, dependencies=[])
        sl.use_effect(add_clear_handler, dependencies=[])

    # expression editor
    with sl.Column(gap="0px") as main:
        with sl.Row(justify="center", style={"align-items": "center"}):
            el = InputTextExposed(
                label="Enter an expression",
                value=expression,
                on_value=set_expression,
                message=message,
                error=errorFound,
                append_icon="mdi-information-outline",
                clearable=True,
                placeholder="teff < 15e3 & (mg_h > -1 | fe_h < -2)",
            )
            add_effect(el)
    return main


@sl.component()
def DatasetSelect(key: str, dataset, set_dataset) -> ValueElement:
    """Select box for pipeline, also sets columns on dataset change."""
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
    """Select box with callback for filters."""
    subset = SubsetState.subsets.value[key]
    df = subset.df
    _, set_flagfilter = use_subset(id(df), key, "flags", write_only=True)
    flags, set_flags = (
        subset.flags,
        lambda arg: SubsetState.update_subset(key, flags=arg),
    )

    def update_flags():
        filters = []
        # TODO: relocate this somewhere better, like into a lookup dataclass or a file
        # get the flag lookup
        if flags:
            for flag in flags:
                # Skip iteration if the subset's dataset is 'best' and the flag is 'Purely non-flagged'
                if (subset.dataset == "best") and (flag
                                                   == "purely non-flagged"):
                    continue
                filters.append(flagList[flag])

            # Determine the final concatenated filter
            if filters:
                # Join the filters with ")&(" and wrap them in outer parentheses
                concat_filter = f"(({')&('.join(filters)}))"
                concat_filter = df[concat_filter]
                if invert.value:
                    concat_filter = ~concat_filter
            else:
                concat_filter = None
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
    """Holds expansion panels for complex filtering"""
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
    dataset, set_dataset = (
        subset.dataset,
        lambda arg: SubsetState.update_subset(key, dataset=arg),
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
        logger.info(f"MAPPER: {mapper}")
        logger.info(f"CARTON: {carton}")
        start = timer()
        if len(mapper) != 0 or len(carton) != 0:
            # mask
            if len(mapper) == 0:
                mask = mapping["alt_name"].isin(carton).values
            elif len(carton) == 0:
                mask = mapping["mapper"].isin(mapper).values
            else:
                mask = operator_map[combotype](
                    mapping["mapper"].isin(mapper).values,
                    mapping["alt_name"].isin(carton).values,
                )

            # determine active bits via mask and get flag_number & offset
            # NOTE: hardcoded nbits as 8, and nflags as 57
            bits = np.arange(len(mapping))[mask]
            num, offset = np.divmod(bits, 8)
            setbits = 57 > num  # ensure bits in flags

            # construct hashmap for each unique flag
            filters = np.zeros(57, dtype="uint8")
            unique_nums, indices = np.unique(num[setbits], return_inverse=True)
            for i, unique in enumerate(unique_nums):
                offsets = 1 << offset[setbits][indices == i]
                filters[unique] = np.bitwise_or.reduce(offsets)

            cmp_filter = df.func.check_flags(df["sdss5_target_flags"], filters)
        else:
            cmp_filter = None

        # invert if requested
        if invert.value:
            set_cmfilter(~cmp_filter)
        else:
            set_cmfilter(cmp_filter)

        logger.info(f"CM filter took {timer() - start:.4f} seconds")

        return cmp_filter

    result = sl.lab.use_task(update_cm,
                             dependencies=[df, mapper, carton, invert.value])

    open, set_open = sl.use_state([])
    with rv.ExpansionPanels(flat=True,
                            multiple=True,
                            v_model=open,
                            on_v_model=set_open) as main:
        DatasetSelect(key, dataset, set_dataset)
        with rv.ExpansionPanel():
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
