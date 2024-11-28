"""Holds specific filter components"""

import operator
import os
import glob
import re
from functools import reduce
from typing import cast

import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement

from ...dataclass import Alert, State, SubsetState, use_subset
from ..textfield import InputTextExposed
from ...util import _datapath
from .autocomplete import AutocompleteSelect, SingleAutocomplete
from .glossary import Help
from .vc_ui import VirtualColumnsPanel

__all__ = [
    "ExprEditor", "TargetingFiltersPanel", "PivotTablePanel", "DatasetSelect"
]

operator_map = {"AND": operator.and_, "OR": operator.or_, "XOR": operator.xor}


@sl.component()
def ExprEditor(key: str, invert) -> ValueElement:
    """Expression editor."""
    # state for expreditor
    subset = SubsetState.subsets.value[key]
    df = subset.df

    _, set_expfilter = use_subset(id(df), key, "expr", write_only=True)

    expression, set_expression = subset.expression, lambda arg: SubsetState.update_subset(
        key, expression=arg)

    error, set_error = sl.use_state(cast(str, None))

    # Expression Editor thread
    def update_expr():
        """
        Validates if the expression is valid, and returns
        a precise error message for any issues in the expression.
        """
        columns = subset.df.get_column_names()
        try:
            if expression is None or expression == "" or expression == 'None':
                set_expfilter(None)
                set_expression('')
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

    result: sl.Result[bool] = sl.use_thread(
        update_expr, dependencies=[expression, invert.value])
    if result.state == sl.ResultState.FINISHED:
        if result.value:
            errorFound = False
            message = "Valid expression entered"
        elif result.value is None:
            errorFound = False
            message = "No expression entered. Filter unset."
        else:
            errorFound = True
            message = f"Invalid expression entered: {error}"

    elif result.state == sl.ResultState.ERROR:
        errorFound = True
        message = f"Backend failure occurred: {result.error}"
    else:
        # processing
        errorFound = False
        message = None

    def add_effect(el: sl.Element):

        def add_append_handler():

            def on_click(widget, event, data):
                Help.update('expressions')

            widget = sl.get_widget(el)
            widget.on_event("click:append", on_click)

            def cleanup():
                widget.on_event("click:append", on_click, remove=True)

            return cleanup

        def add_clear_handler():

            def on_click(widget, event, data):
                set_expression('')
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
        with sl.Row(justify='center', style={"align-items": "center"}):
            el = InputTextExposed(
                label="Enter an expression",
                value=expression,
                on_value=set_expression,
                message=message,
                error=errorFound,
                append_icon='mdi-information-outline',
                clearable=True,
                placeholder='teff < 15e3 & (mg_h > -1 | fe_h < -2)')
            add_effect(el)
    return main


@sl.component()
def DatasetSelect(key, dataset, set_dataset) -> ValueElement:
    """Select box for pipeline."""
    subset = SubsetState.subsets.value[key]
    df = subset.df
    datapath = sl.use_memo(_datapath, dependencies=[])

    def fetch_names():
        regex = re.compile(
            fr"astraAll{subset.datatype.capitalize()}([A-Za-z]+)-")
        names = [
            regex.match(os.path.basename(filename)).group(1) for filename in
            glob.glob(f"{datapath}/{State.release.value}/*.hdf5")
        ]
        return names

    names = sl.use_memo(fetch_names, dependencies=[])

    #TODO: effect here to change loaded df?

    return SingleAutocomplete(label='Dataset',
                              values=names,
                              value=dataset,
                              on_value=set_dataset)


@sl.component()
def FlagSelect(key: str, invert) -> ValueElement:
    """Select box with callback for filters."""
    subset = SubsetState.subsets.value[key]
    df = subset.df
    _, set_flagfilter = use_subset(id(df), key, "flags", write_only=True)
    flags, set_flags = subset.flags, lambda arg: SubsetState.update_subset(
        key, flags=arg)

    def update_flags():
        filters = []
        # TODO: relocate this somewhere better, like into a lookup dataclass or a file
        flagList = {
            'SDSS5 only': "release=='sdss5'",
            'SNR > 50': "snr>=50",
            'Purely non-flagged': 'result_flags==0',
            #'No APO 1m': "telescope!='apo1m'", # WARNING: this one doesn't work for some reason, maybe it's not string; haven't checked
            'No bad flags': 'flag_bad==0',
            'Vmag < 13': 'v_jkc_mag<=13'
        }
        # get the flag lookup
        if len(flags) > 0:
            for flag in flags:
                # WARNING: terrible bypass of bug; astraBest does not contain 'result_flags'
                if (subset.dataset.lower()
                        == 'best') & (flag == 'Purely non-flagged'):
                    continue
                filters.append(flagList[flag])
            if len(filters) > 0:
                # string join
                print('FLAG FILTERS', filters)
                concat_filter = ")&(".join(filters)
                concat_filter = "((" + concat_filter + "))"
                concat_filter = df[concat_filter]
                if invert.value:
                    concat_filter = ~concat_filter
            else:
                concat_filter = None
        else:
            concat_filter = None

        set_flagfilter(concat_filter)
        return

    sl.use_thread(update_flags, dependencies=[flags, invert.value])

    return AutocompleteSelect(
        flags,
        set_flags,
        df=[
            'SDSS5 only',
            'SNR > 50',
            'Purely non-flagged',  #'No APO 1m',
            'No bad flags',
            'Vmag < 13'
        ],
        expr='foobar',
        field='Quick Flags',
        multiple=True)


@sl.component()
def TargetingFiltersPanel(key: str, invert) -> ValueElement:
    """Holds expansion panels for complex filtering"""
    mapping = State.mapping.value
    subset = SubsetState.subsets.value[key]
    df = subset.df
    _, set_cmfilter = use_subset(id(df), key, "cartonmapper", write_only=True)
    # handlers for mapper/carton/data/setflags
    mapper, set_mapper = subset.mapper, lambda arg: SubsetState.update_subset(
        key, mapper=arg)
    carton, set_carton = subset.carton, lambda arg: SubsetState.update_subset(
        key, carton=arg)
    dataset, set_dataset = subset.dataset, lambda arg: SubsetState.update_subset(
        key, dataset=arg)
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

        # convert chosens to bool mask
        cmp_filter = None
        if len(mapper) == 0 and len(carton) == 0:
            set_cmfilter(None)
            return

        # mapper + cartons
        elif len(mapper) != 0 or len(carton) != 0:
            c = mapping["alt_name"].isin(carton).values
            m = mapping["mapper"].isin(mapper).values

            # mask
            if len(mapper) == 0:
                mask = c
            elif len(carton) == 0:
                mask = m
            else:
                mask = operator_map[combotype](m, c)

            bits = np.arange(len(mapping))[mask]

            # get flag_number & offset
            # NOTE: hardcoded nbits as 8, and nflags as 57
            # TODO: in future, change to read from mappings parquet
            num, offset = np.divmod(bits, 8)
            setbits = 57 > num  # ensure bits in flags

            # construct hashmap for each unique flag
            filters = np.zeros(57).astype("uint8")
            for unique in np.unique(num[setbits]):
                # ANDs all the bitshifted values for the given unique flag
                offsets = 1 << offset[setbits][np.where(
                    num[setbits] == unique)]
                actives = reduce(
                    operator.or_,
                    offsets)  # INFO: this is an OR operation PER bit
                if actives == 0:
                    continue  # skip
                filters[unique] = (
                    actives  # the required active bit(s) ACTIVES for bitmask position "UNIQUE"
                )

            # generate a filter based on the vaex-defined flag combiner
            cmp_filter = df.func.check_flags(df["sdss5_target_flags"], filters)

        # invert if requested
        if invert.value:
            set_cmfilter(~cmp_filter)
        else:
            set_cmfilter(cmp_filter)

        return

    sl.use_thread(update_cm,
                  dependencies=[mapper, carton, dataset, invert.value])

    open, set_open = sl.use_state([])
    with rv.ExpansionPanels(flat=True,
                            multiple=True,
                            v_model=open,
                            on_v_model=set_open) as main:
        DatasetSelect(key, dataset, set_dataset)
        VirtualColumnsPanel(key)
        with rv.ExpansionPanel():
            rv.ExpansionPanelHeader(children=["Targeting Filters"])
            with rv.ExpansionPanelContent():
                if State.mapping.value is None:
                    sl.Warning(
                        dense=True,
                        label=
                        "Mappings file not found! Please contact server admins.",
                    )
                else:
                    with sl.Column(gap="2px"):
                        AutocompleteSelect(mapper,
                                           set_mapper,
                                           df=State.mapping.value,
                                           expr='mapper',
                                           field='Mapper',
                                           multiple=True)
                        AutocompleteSelect(carton,
                                           set_carton,
                                           df=State.mapping.value,
                                           expr='alt_name',
                                           field='Carton',
                                           multiple=True)
                        FlagSelect(key, invert)

    return main


@sl.component()
def PivotTablePanel() -> ValueElement:
    """Holds solara PivotTable in expansion panel. Deprecated (maybe implement again in future)"""

    df = None  #State.df.value
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
