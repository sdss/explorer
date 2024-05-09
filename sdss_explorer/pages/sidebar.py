from functools import reduce
from timeit import default_timer as timer
import operator

import solara as sl
from solara.lab import ConfirmationDialog, Menu
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv

from .state import State, load_datapath, VCData, Alert
from .dialog import Dialog
from .editor import ExprEditor
from .subsets import use_subset, remove_subset

operator_map = {"AND": operator.and_, "OR": operator.or_, "XOR": operator.xor}


@vx.register_function()
def check_flags(flags, vals):
    return np.any(np.logical_and(flags, vals), axis=1)


@sl.component()
def SubsetMenu():
    """Control and display subset cards"""
    add = sl.use_reactive(False)
    name, set_name = sl.use_state("")

    def add_subset():
        if name not in State.subsets.value:
            State.subsets.value.append(name)
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
                SubsetCard(subset, State.create_ss_remover(subset))
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
def SubsetCard(name, deleter):
    """Card containing functions for a single subset."""
    df = State.df.value
    filter, set_filter = use_subset(id(df), name, "summary")
    invert, set_invert = sl.use_state(False)
    delete = sl.use_reactive(False)
    open, set_open = sl.use_state(False)

    # filter logic
    if filter:
        filtered = True
        dff = df[filter]
    else:
        filtered = False
        dff = df
    progress = len(dff) / len(df) * 100
    summary = f"{len(dff):,}"

    # main ui
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
            sl.ProgressLinear(value=progress, color="blue")
            ExprEditor(name)
            with rv.ExpansionPanels():
                with rv.ExpansionPanel():
                    rv.ExpansionPanelHeader(children=["Carton/Mapper/Dataset"])
                    with rv.ExpansionPanelContent():
                        CartonMapperSelect(name)

            # delete and other settings
            with rv.Row(style_="width: 100%; height: 100%"):
                # quick filter menu
                rv.Spacer()

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

    if df is not None:
        with sl.Row(style={"align-items": "center"}):
            sl.FileDownload(
                get_data,
                filename="apogeenet_filtered.csv",
                label="Download table",
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
def CartonMapperSelect(name):
    """Filter by carton and mapper. May be merged into another panel in future."""
    df = State.df.value
    filter, set_filter = use_subset(id(df), name, "cartonmapper")
    mapper, set_mapper = sl.use_state([])
    carton, set_carton = sl.use_state([])
    dataset, set_dataset = sl.use_state([])
    combotype, set_combotype = sl.use_state("AND")
    mapping = sl.use_memo(
        lambda: vx.open(f"{load_datapath()}/mappings.parquet"),
        dependencies=[])

    def update_filter():
        # convert chosens to bool mask
        print("MapperCarton ::: starting filter update")
        print(mapper, carton)

        cmp_filter = None
        if len(mapper) == 0 and len(carton) == 0 and len(dataset) == 0:
            print("No selections: empty exit case")
            set_filter(None)
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
        set_filter(cmp_filter)

        return

    sl.use_thread(update_filter,
                  dependencies=[mapper, carton, dataset, combotype])

    with sl.Column(gap="2px") as main:
        with sl.Columns([1, 1]):
            sl.SelectMultiple(
                label="Mapper",
                values=mapper,
                on_value=set_mapper,
                dense=True,
                all_values=State.mapping.value["mapper"].unique(),
                classes=['variant="solo"'],
            )
            sl.SelectMultiple(
                label="Dataset",
                values=dataset,
                on_value=set_dataset,
                dense=True,
                all_values=["apogeenet", "thecannon", "aspcap"],
                classes=['variant="solo"'],
            )
        sl.SelectMultiple(
            label="Carton",
            values=carton,
            on_value=set_carton,
            dense=True,
            all_values=State.mapping.value["alt_name"].unique(),
            classes=['variant="solo"'],
        )
        # with sl.ToggleButtonsSingle(
        #        value=combotype,
        #        on_value=set_combotype,
        #        dense=True,
        #        style=dict(width="100%"),
        # ):  # type: ignore
        #    sl.Button(icon_name="mdi-gate-and", icon=True, value="AND")
        #    sl.Button(icon_name="mdi-gate-or", icon=True, value="OR")
        #    sl.Button(icon_name="mdi-gate-xor", icon=True, value="XOR")
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
