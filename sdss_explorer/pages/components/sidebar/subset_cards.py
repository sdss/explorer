"""Subset cards and SubsetState class"""

import operator
import re
from functools import reduce
from typing import Callable, cast

import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
from solara.lab import ConfirmationDialog

from ...dataclass import Alert, State, init_key, use_subset
from ...util import generate_unique_key
from ..dialog import Dialog
from .subset_filters import CartonMapperPanel, DownloadMenu, ExprEditor

operator_map = {"AND": operator.and_, "OR": operator.or_, "XOR": operator.xor}

# context for updater and renamer
updater_context = sl.create_context(print)  # context for forcing updates
rename_context = sl.create_context(
    ("hi", print))  # context for renamer function


def remove_key(d: dict, key: str) -> dict:
    """Function to pop a dict map and return the altered dict via shallow copy"""
    r = dict(d)
    r.pop(key)
    return r


@sl.component()
def SubsetCard(key: str, **kwargs):
    """Holds filter update info, card structure, and calls to options"""
    df = State.df.value
    filter, _set_filter = use_subset(id(df), key, "subset-summary")
    updater = sl.use_context(updater_context)
    name, set_name = sl.use_state(
        State.subsets.value[key])  # instantiation parameter
    sl.provide_context(rename_context, (name, set_name))

    def remove(subset_key):
        """
        q: index of subset in list; variate
        """
        for n, (k, v) in enumerate(State.subsets.value.items()):
            if k == subset_key:
                q = n
                break

        # pop from subset name mappings
        State.subsets.value = remove_key(State.subsets.value, subset_key)
        print(State.subsets.value)

        # slice the card list
        SubsetState.subset_cards.value = (
            SubsetState.subset_cards.value[:q] +
            SubsetState.subset_cards.value[q + 1:])

        # force update
        updater()
        SubsetState.update_subset_names()  # forcefully update subsetname list

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
            SubsetOptions(key, lambda: remove(key), **kwargs).key(key)
    return main


class SubsetState:
    subset_cards = sl.reactive([
        SubsetCard(
            init_key,
            **{
                "expression": "teff < 15e3",
                "mapper": ["mwm"]
            },
        ).key(init_key)
    ])

    @staticmethod
    def add_subset(name: str, **kwargs):
        """Adds subset and subsetcard, generating new unique key for subset. Boolean return for success."""
        if name not in State.subset_names.value and len(name) > 0:
            # generate unique key
            key = generate_unique_key(name)

            # add to name, mapping + object list
            # NOTE: must be done in this order
            State.subsets.value[key] = name
            SubsetState.subset_cards.value = [
                *SubsetState.subset_cards.value,
                SubsetCard(key, **kwargs).key(key),
            ]

            return True
        elif name == "":
            Alert.update("Please enter a name for the subset.",
                         color="warning")
        else:
            Alert.update("Subset with name already exists!", color="error")
        return False

    def update_subset_names():
        State.subset_names.set(list(State.subsets.value.values()))
        print(State.subset_names.value)
        return

    @staticmethod
    def rename_subset(key: str, new_name: str):
        print("RENAME: key=", key)
        print("keys", State.subsets.value.keys())
        if key not in State.subsets.value.keys():
            Alert.update("BUG: subset rename failed! Key not in hashmap.",
                         color="error")
            return False
        else:
            State.subsets.value[key] = new_name
            return True


@sl.component()
def SubsetOptions(key: str, deleter: Callable, **kwargs):
    """
    Contains all subset configuration threads and state variables,
    including expression, cartonmapper, clone and delete.

    Grouped to single namespace to add clone functionality.

    Inputs:
        :key: key for subset
        :deleter: deletion functions
        :kwargs: initialization parameters for state variables

    state variables
    :invert: whether filter is inverted
    :expression: expression for expression editor
    :error: expression editor error message
    :carton: list of selected cartons
    :mapper: list of selected mappers
    :dataset: list of selected datasets
    :delete: deletion c-dialog v-slot reactive
    :rename: rename dialog v-slot reactive

    threads/functions
    :clone_subset: callback to clone a subset on button click
    :update_expr: thread to update expression filter on expression change
    :update_cm: thread to update cartonmapper filter on selection changes
    """
    df = State.df.value
    mapping = State.mapping.value
    updater = sl.use_context(updater_context)  # fetch update forcer
    name, set_name = sl.use_context(rename_context)  # fetch renme function

    # dialog states
    delete = sl.use_reactive(False)
    rename = sl.use_reactive(False)
    newname, set_newname = sl.use_state("")  # rename dialog state

    # filter settings/subfilters
    invert = sl.use_reactive(False)
    _expfilter, set_expfilter = use_subset(id(df),
                                           key,
                                           "expr",
                                           write_only=True)
    _cmfilter, set_cmfilter = use_subset(id(df),
                                         key,
                                         "cartonmapper",
                                         write_only=True)

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

    # clone and rename methods (deletion defined previously)

    def clone_subset():
        """Self cloner function"""
        if SubsetState.add_subset(
                "Copy of " + name,
                **{
                    "mapper": mapper,
                    "carton": carton,
                    "dataset": dataset,
                    "expression": expression,
                },
        ):
            updater()  # force update
            SubsetState.update_subset_names(
            )  # forcefully update subsetname list

        return

    def rename_subset():
        """Wrapper for renaming subsets via dataclass method."""
        if SubsetState.rename_subset(key, newname):
            rename.set(False)
            set_name(newname)
            set_newname("")
            updater()  # force update; could do without it
            SubsetState.update_subset_names(
            )  # forcefully update subsetname list
        return

    def update_n_subsets():
        return len(State.subset_names.value)

    # NOTE: callback to bypass reactive monitoring limitations
    n_subsets = sl.use_memo(
        update_n_subsets,
        dependencies=[State.subset_names.value,
                      len(State.subset_names.value)],
    )

    # Expression Editor thread
    def update_expr():
        """
        Validates if the expression is valid, and returns
        a precise error message for any issues in the expression.
        """
        columns = State.columns.value
        try:
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

    # Carton Mapper thread
    def update_cm():
        # convert chosens to bool mask

        cmp_filter = None
        if len(mapper) == 0 and len(carton) == 0 and len(dataset) == 0:
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

        if len(dataset) > 0:
            if cmp_filter is not None:
                cmp_filter = operator_map[combotype](
                    cmp_filter, df["dataset"].isin(dataset))
            else:
                cmp_filter = df["dataset"].isin(dataset)

        # invert if requested
        if invert.value:
            set_cmfilter(~cmp_filter)
        else:
            set_cmfilter(cmp_filter)

        return

    sl.use_thread(update_cm,
                  dependencies=[mapper, carton, dataset, invert.value])

    # User facing
    with sl.Column() as main:
        ExprEditor(expression, set_expression, error, result)
        # complex option panels
        with rv.ExpansionPanels(flat=True):
            # PANEL1: carton mapper
            CartonMapperPanel(mapper, set_mapper, carton, set_carton, dataset,
                              set_dataset)
        # delete & clone buttons
        with rv.Row(style_="width: 100%; height: 100%"):
            # download button
            DownloadMenu()

            # invert button
            with sl.Tooltip("Invert the filters of this subset"):
                sl.Button(
                    label="",
                    icon_name="mdi-invert-colors-off"
                    if invert.value else "mdi-invert-colors",
                    color="red" if invert.value else None,
                    icon=True,
                    text=True,
                    on_click=lambda: invert.set(not invert.value),
                )

            # spacer
            rv.Spacer()

            # rename button
            with sl.Tooltip("Rename this subset"):
                sl.Button(
                    label="",
                    icon_name="mdi-rename-box",
                    icon=True,
                    text=True,
                    on_click=lambda: rename.set(True),
                )

            # clone button
            with sl.Tooltip("Clone this subset"):
                sl.Button(
                    label="",
                    icon_name="mdi-content-duplicate",
                    icon=True,
                    text=True,
                    on_click=clone_subset,
                )

            # delete button
            with sl.Tooltip("Delete this subset"):
                sl.Button(
                    label="",
                    icon_name="mdi-delete-outline",
                    icon=True,
                    text=True,
                    disabled=True if n_subsets <= 1 else False,
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

        # rename dialog
        with Dialog(
                rename,
                title="Enter a new name for this subset",
                close_on_ok=False,
                on_ok=rename_subset,
                on_cancel=lambda: set_newname(""),
        ):
            sl.InputText(
                label="Subset name",
                value=newname,
                on_value=set_newname,
            )
    return main
