from typing import cast, Union
from functools import reduce
from timeit import default_timer as timer
import operator
import re

import solara as sl
from solara.lab import ConfirmationDialog, Menu
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv
from solara.hooks.misc import use_force_update

from .state import State, load_datapath, VCData, Alert
from .dialog import Dialog
from .subsets import use_subset, remove_subset

operator_map = {"AND": operator.and_, "OR": operator.or_, "XOR": operator.xor}

updater_context = sl.create_context(print)


@vx.register_function()
def check_flags(flags, vals):
    return np.any(np.logical_and(flags, vals), axis=1)


@sl.component()
def SubsetMenu():
    """Control and display subset cards"""
    add = sl.use_reactive(False)
    name, set_name = sl.use_state("")
    updater = use_force_update()
    updater_context.provide(updater)

    def add_subset():
        if name not in State.subsets.value:
            State.subsets.value.append((name, {}))
            add.set(False)
            close()
        else:
            Alert.update("Subset with name already exists!", color="error")
        return

    def close():
        """Dialog close handler, resetting state vars"""
        add.set(False)
        set_name("")
        return

    with sl.Column(gap="0px") as main:
        with rv.Card(class_="justify-center",
                     style_="width: 100%; height: 100%"):
            rv.CardTitle(
                class_="justify-center",
                children=["Subsets"],
            )
            with rv.CardText():
                sl.Button(label="Add new subset",
                          on_click=lambda: add.set(True),
                          block=True)
        with rv.ExpansionPanels(popout=True):
            for subset in State.subsets.value:
                SubsetCard(subset[0], State.create_ss_remover(subset[0]),
                           **subset[1])
        with Dialog(
                add,
                title="Enter a name for the new subset",
                close_on_ok=False,
                on_ok=add_subset,
        ):
            sl.InputText(
                label="Subset name",
                value=name,
                on_value=set_name,
            )

    return main


@sl.component()
def SubsetCard(name: str, deleter, **kwargs):
    """Holds filter update info, card structure, and calls to options"""
    df = State.df.value
    filter, _set_filter = use_subset(id(df), name, "subset-summary")

    # progress bar logic
    if filter:
        # filter from plots or self
        filtered = True
        dff = df[filter]
    else:
        # not filtered at all
        filtered = False
        dff = df
    progress = len(dff) / len(df) * 100
    summary = f"{len(dff):,}"
    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            with sl.Row(gap="0px"):
                rv.Col(cols="4", children=[name])
                rv.Col(
                    cols="8",
                    class_="text--secondary",
                    children=[
                        rv.Icon(
                            children=["mdi-filter"],
                            style_="opacity: 0.1" if not filtered else "",
                        ),
                        summary,
                    ],
                )

        with rv.ExpansionPanelContent():
            # filter bar
            sl.ProgressLinear(value=progress, color="blue")
            SubsetOptions(name, deleter, **kwargs)
    return main


@sl.component()
def SubsetOptions(name: str, deleter, **kwargs):
    """
    Contains all subset configuration, including expression,
    cartonmapper, clone and delete.

    Grouped to single namespace to minimize subset listeners.

    TODO DOCS

    state variables
    :filter: cross-filters from plot views corresponding to subset
    :invert: whether filter is inverted
    :delete: deletion confirmation v-slot reactive
    :expression: expression for expression editor
    :error: expression editor error message
    :carton: list of selected cartons
    :mapper: list of selected mappers
    :dataset: list of selected datasets

    threads/functions
    ::
    """
    df = State.df.value
    mapping = State.mapping.value
    filter, set_filter = use_subset(id(df), name, "subsetcard")
    updater = sl.use_context(updater_context)

    # card settings
    invert, set_invert = sl.use_state(False)
    delete = sl.use_reactive(False)
    open, set_open = sl.use_state(False)

    # sub-filters
    expfilter, set_expfilter = sl.use_state(cast(vx.Expression, None))
    cmfilter, set_cmfilter = sl.use_state(cast(vx.Expression, None))

    # state for expreditor
    expression, set_expression = sl.use_state(
        kwargs.setdefault("expression", ""))
    error, set_error = sl.use_state(cast(str, None))

    # state for cartonmapper
    mapper, set_mapper = sl.use_state(kwargs.setdefault("mapper", []))
    carton, set_carton = sl.use_state(kwargs.setdefault("carton", []))
    dataset, set_dataset = sl.use_state(kwargs.setdefault("dataset", []))
    combotype = (
        "AND"  # NOTE: remains for functionality as potential state var (in future)
    )

    # main filter update thread
    def update_filter():
        """Combines filters and updates main out-going filter, and creates self-reduction"""
        combined_filter = [expfilter, cmfilter]
        combined_filter = [
            elem for elem in combined_filter if elem is not None
        ]

        if len(combined_filter) > 0:
            combined_filter = reduce(operator.and_, combined_filter[1:],
                                     combined_filter[0])
            set_filter(combined_filter)
        else:
            set_filter(None)

    sl.use_thread(update_filter, dependencies=[expfilter, cmfilter])

    def clone_subset():
        """Self cloner function"""
        State.subsets.value.append((
            "Copy of " + name,
            {
                "mapper": mapper,
                "carton": carton,
                "dataset": dataset,
                "expression": expression,
            },
        ))
        updater()
        return

    # Expression Editor thread
    def update_expr():
        """
        Validates if the expression is valid, and returns
        a precise error message for any issues in the expression.
        """
        print("EXPR: start")
        columns = State.columns.value
        try:
            print(expression)
            start = timer()
            if expression is None or expression == "":
                set_expfilter(None)
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
            print("EXPR: validation = ", timer() - start)

            # set filter & exit
            start = timer()
            set_expfilter(df[expr])
            print("EXPR: set! time= ", timer() - start)
            return True

        except AssertionError as e:
            # INFO: it's probably better NOT to unset filters if assertions fail.
            # set_filter(None)
            set_error(e)  # saves error msg to state
            return False
        except SyntaxError as e:
            set_error("modifier at end of sequence with no expression")
            return False

    result: sl.Result[bool] = sl.use_thread(update_expr,
                                            dependencies=[expression])

    # Carton Mapper thread
    def update_cm():
        # convert chosens to bool mask
        print("MapperCarton ::: starting filter update")
        print(mapper, carton)

        cmp_filter = None
        if len(mapper) == 0 and len(carton) == 0 and len(dataset) == 0:
            print("No selections: empty exit case")
            set_cmfilter(None)
            return

        # mapper + cartons
        elif len(mapper) != 0 or len(carton) != 0:
            start = timer()
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
            print("Timer for bit selection via mask:",
                  round(timer() - start, 5))

            start = timer()
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

            print("Timer for active mask creation:", round(timer() - start, 5))

            # generate a filter based on the vaex-defined flag combiner
            start = timer()
            cmp_filter = df.func.check_flags(df["sdss5_target_flags"], filters)
            print("Timer for expression generation:",
                  round(timer() - start, 5))

        if len(dataset) > 0:
            if cmp_filter is not None:
                cmp_filter = operator_map[combotype](
                    cmp_filter, df["dataset"].isin(dataset))
            else:
                cmp_filter = df["dataset"].isin(dataset)
        set_cmfilter(cmp_filter)

        return

    sl.use_thread(update_cm, dependencies=[mapper, carton, dataset, combotype])

    # User facing
    with sl.Column() as main:
        # expression editor
        with sl.Column(gap="0px"):
            sl.InputText(
                label="Enter an expression",
                value=expression,
                on_value=set_expression,
            )
            if result.state == sl.ResultState.FINISHED:
                if result.value:
                    sl.Success(
                        label="Valid expression entered.",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
                elif result.value is None:
                    sl.Info(
                        label="No expression entered. Filter unset.",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
                else:
                    sl.Error(
                        label=f"Invalid expression entered: {error}",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )

            elif result.state == sl.ResultState.ERROR:
                sl.Error(f"Error occurred: {result.error}")
            else:
                sl.Info("Evaluating expression...")
                rv.ProgressLinear(indeterminate=True)

        # complex option panels
        with rv.ExpansionPanels():
            # PANEL1: carton mapper
            with rv.ExpansionPanel():
                rv.ExpansionPanelHeader(children=["Carton/Mapper/Dataset"])
                with rv.ExpansionPanelContent():
                    with sl.Column(gap="2px"):
                        with sl.Columns([1, 1]):
                            sl.SelectMultiple(
                                label="Mapper",
                                values=mapper,
                                on_value=set_mapper,
                                dense=True,
                                all_values=State.mapping.value["mapper"].
                                unique(),
                                classes=['variant="solo"'],
                            )
                            sl.SelectMultiple(
                                label="Dataset",
                                values=dataset,
                                on_value=set_dataset,
                                dense=True,
                                # TODO: fetch via valis or via df itself
                                all_values=[
                                    "apogeenet", "thecannon", "aspcap"
                                ],
                                classes=['variant="solo"'],
                            )
                        sl.SelectMultiple(
                            label="Carton",
                            values=carton,
                            on_value=set_carton,
                            dense=True,
                            all_values=State.mapping.value["alt_name"].unique(
                            ),
                            classes=['variant="solo"'],
                        )

        with rv.Row(style_="width: 100%; height: 100%"):
            # TODO: change this component to a better button embedded in the below structure
            DownloadMenu()

        # delete & clone buttons
        with rv.Row(style_="width: 100%; height: 100%"):
            # quick filter menu
            rv.Spacer()

            # clone button
            sl.Button(
                label="",
                icon_name="mdi-content-duplicate",
                icon=True,
                text=True,
                on_click=lambda: clone_subset(),
            )

            # delete button
            sl.Button(
                label="",
                icon_name="mdi-delete-outline",
                icon=True,
                text=True,
                disabled=True if len(State.subsets.value) == 1 else False,
                color="red",
                on_click=lambda: delete.set(True),
            )

        # confirmation dialog for deletion
        ConfirmationDialog(
            delete,
            title="Are you sure you want to delete this subset?",
            ok="yes",
            cancel="no",
            on_ok=deleter,
        )
    return main


@sl.component()
def DownloadMenu():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "download")
    if filter:
        dff = df[filter]
    else:
        dff = df

    def get_data():
        dfp = dff.to_pandas()
        return dfp.to_csv(index=False)

    return sl.FileDownload(
        get_data,
        filename="ipl3_filtered.csv",
        label="Download",
    )


@sl.component()
def QuickFilterMenu(name):
    """
    Apply quick filters via check boxes.
    """
    df = State.df.value
    # TODO: find out how flags work, currently using 1 col as plceholders:
    flag_cols = ["result_flags"]
    _filter, set_filter = use_subset(id(df), name, "quickflags")

    # Quick filter states
    flag_nonzero, set_flag_nonzero = sl.use_state(False)
    flag_snr50, set_flag_snr50 = sl.use_state(False)

    def reset_filters():
        set_flag_nonzero(False)
        set_flag_snr50(False)

    def work():
        filters = []
        flags = [flag_nonzero, flag_snr50]

        # all false
        if np.all(np.logical_not(flags)):
            set_filter(None)
            return

        # flag out all nonzero
        if flag_nonzero:
            for flag in flag_cols:
                filters.append(df[f"({flag}==0)"])
        if flag_snr50:
            filters.append(df["(snr > 50)"])
        concat_filter = reduce(operator.and_, filters[1:], filters[0])
        set_filter(concat_filter)
        return

    # apply thread to filtering logic so it only runs on rerenders
    sl.use_thread(
        work,
        dependencies=[flag_nonzero, flag_snr50],
    )

    with rv.Card() as main:
        with rv.CardTitle(children=["Quick filters"]):
            rv.Icon(children=["mdi-filter-plus-outline"])
        with rv.CardText():
            sl.Checkbox(
                label="All flags zero",
                value=flag_nonzero,
                on_value=set_flag_nonzero,
            )
            sl.Checkbox(label="SNR > 50",
                        value=flag_snr50,
                        on_value=set_flag_snr50)
    return main


@sl.component()
def PivotTablePanel():
    df = State.df.value
    print(type(df))
    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-table-plus"])
            with rv.CardTitle(children=["Pivot Table"]):
                pass
        with rv.ExpansionPanelContent():
            if ~isinstance(df, dict):
                # BUG: says the df is a dictionary when it isnt, no idea why this occurs
                # NOTE: the fix below fixes it, but is weird
                if type(df) != dict:
                    sl.PivotTableCard(df, y=["telescope"], x=["release"])
    return main


def VirtualColumnList():
    """Renders list of created virtual columns with delete buttons"""
    # NOTE: this should be efficient, but it could also just not be
    print(VCData.columns.value)
    with sl.Column(gap="0px"):
        for name, expression in VCData.columns.value:
            with rv.Card():
                rv.CardTitle(children=[name])
                rv.CardSubtitle(children=[expression])
                with rv.CardActions(class_="justify-center"):
                    sl.Button(
                        label="",
                        icon_name="mdi-delete-outline",
                        text=True,
                        icon=True,
                        color="red",
                        on_click=lambda: VCData.delete_column(
                            name, expression),
                    )


@sl.component()
def VirtualColumnsPanel():
    df = State.df.value
    open, set_open = sl.use_state(False)
    expression, set_expression = sl.use_state("")
    name, set_name = sl.use_state("")
    error, set_error = sl.use_state("")
    active = sl.use_reactive(False)

    def validate():
        "Ensure syntax is correct"
        try:
            if expression == "" and name == "":
                return None
            # none cases
            assert name != "", "no name given"
            # check name
            assert name not in df.get_column_names(), "name already exists"

            # validate via AST
            assert expression != "", "no expression set"
            df.validate_expression(expression)

            # alert user about powers
            if r"^" in expression:
                Alert.update(
                    "'^' is a bit operator. If you're looking to use powers, use '**' (Python syntax) instead.",
                    color="warning",
                )

            # set button to active
            active.set(True)
            return True

        except Exception as e:
            set_error(str(e))
            return False

    def add_column():
        """Adds virtual column"""
        df.add_virtual_column(name, expression)
        VCData.add_column(name, expression)
        close()

    result: sl.Result = sl.use_thread(validate,
                                      dependencies=[expression, name])

    def update_columns():
        """Manually updates columns on VCData update"""
        df = State.df.value
        print("current VCD:", VCData.columns.value)
        columns = df.get_column_names(virtual=False)
        virtuals = list()
        for name, _expr in VCData.columns.value:
            virtuals.append(name)
        print("current virtuals:", virtuals)
        State.columns.value = virtuals + columns

    sl.use_thread(
        update_columns,
        dependencies=[len(VCData.columns.value)],
    )

    def close():
        """Clears state variables and closes dialog."""
        set_open(False)
        set_name("")
        set_expression("")
        active.set(False)

    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=["Virtual calculations"])
        with rv.ExpansionPanelContent():
            VirtualColumnList()
            btn = sl.Button(label="Add virtual column",
                            block=True,
                            on_click=lambda: set_open(True))
            sl.Button

        with Dialog(
                open,
                title="Add virtual column",
                on_cancel=close,
                ok="Add",
                close_on_ok=False,
                on_ok=add_column,
                persistent=True,
                ok_enable=active,
        ):
            sl.InputText(
                label="Enter an name for the new column.",
                value=name,
                on_value=set_name,
            )
            sl.InputText(
                label="Enter an expression for the new column.",
                value=expression,
                on_value=set_expression,
            )
            if result.state == sl.ResultState.FINISHED:
                if result.value:
                    sl.Success(
                        label="Valid expression & name entered.",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
                elif result.value is None:
                    sl.Info(
                        label="Enter an expression and a name for the column.",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
                else:
                    sl.Error(
                        label=f"Invalid expression/name entered: {error}",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
            elif result.state == sl.ResultState.ERROR:
                sl.Error(f"Error occurred: {result.error}")
            else:
                sl.Info("Evaluating expression...")
                rv.ProgressLinear(indeterminate=True)
    return main


@sl.component()
def sidebar():
    df = State.df.value
    with sl.Sidebar() as main:
        if df is not None:
            SubsetMenu()
            rv.Divider()
            with rv.ExpansionPanels(accordion=True, multiple=True):
                VirtualColumnsPanel()
        else:
            sl.Info("No data loaded.")
    return main
