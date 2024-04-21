from functools import reduce
from timeit import default_timer as timer
import operator

import solara as sl
from solara.lab import use_task
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv

from .state import State, load_datapath
from .dialog import Dialog
from .editor import ExprEditor, SumCard


@vx.register_function()
def check_flags(flags, vals):
    return np.any(np.logical_and(flags, vals), axis=1)


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
def QuickFilterMenu():
    """
    Apply quick filters via check boxes.
    """
    df = State.df.value
    # TODO: find out how flags work, currently using 3 cols as plceholders:
    flag_cols = ["result_flags", "flag_bad", "flag_warn"]
    _filter, set_filter = sl.use_cross_filter(id(df), "quickflags")

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

    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-filter-plus-outline"])
            with rv.CardTitle(children=["Quick filters"]):
                pass
        with rv.ExpansionPanelContent():
            sl.Checkbox(
                label="All flags zero",
                value=flag_nonzero,
                on_value=set_flag_nonzero,
            )
            sl.Checkbox(label="SNR > 50",
                        value=flag_snr50,
                        on_value=set_flag_snr50)
    return


@sl.component()
def CartonMapperPanel():
    """Filter by carton and mapper. May be merged into another panel in future."""
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "cartonmapper")
    mapper, set_mapper = sl.use_state([])
    carton, set_carton = sl.use_state([])
    dataset, set_dataset = sl.use_state([])
    combotype, set_combotype = sl.use_state("OR")
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

            if combotype.lower() == "or":
                operation = operator.or_
            elif combotype.lower() == "xor":
                operation = np.logical_xor
            elif combotype.lower() == "and":
                operation = operator.and_
            else:
                raise ValueError(
                    "illegal combination type set for combining mapper/carton filter"
                )

            # mask
            if len(mapper) == 0:
                mask = c
            elif len(carton) == 0:
                mask = m
            else:
                mask = operation(m, c)

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
                actives = reduce(operator.or_,
                                 offsets)  # INFO: must always be OR
                if actives == 0:
                    continue  # skip
                filters[unique] = (
                    actives  # the required active bit(s) ACTIVES for bitmask position "UNIQUE"
                )

            print("Timer for active mask creation:", round(timer() - start, 5))

            # generate a filter based on the vaex function defined above

            start = timer()
            cmp_filter = df.func.check_flags(df["sdss5_target_flags"], filters)
            print("Timer for expression generation:",
                  round(timer() - start, 5))

        if len(dataset) > 0:
            if cmp_filter is not None:
                cmp_filter = operation(cmp_filter, df["dataset"].isin(dataset))
            else:
                cmp_filter = df["dataset"].isin(dataset)
        set_filter(cmp_filter)

        return

    sl.use_thread(update_filter,
                  dependencies=[mapper, carton, dataset, combotype])

    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-magnify-scan"])
            with rv.CardTitle(children=["Targeting catalogs"]):
                pass
        with rv.ExpansionPanelContent():
            # mappers
            with sl.Columns([1, 1]):
                sl.SelectMultiple(
                    label="Mapper",
                    values=mapper,
                    on_value=set_mapper,
                    all_values=State.mapping.value["mapper"].unique(),
                    classes=['variant="solo"'],
                )
                sl.SelectMultiple(
                    label="Dataset",
                    values=dataset,
                    on_value=set_dataset,
                    all_values=["apogeenet", "thecannon", "aspcap"],
                    classes=['variant="solo"'],
                )
            sl.SelectMultiple(
                label="Carton",
                values=carton,
                on_value=set_carton,
                all_values=State.mapping.value["alt_name"].unique(),
                classes=['variant="solo"'],
            )
            sl.Select(
                label="Reduction method",
                value=combotype,
                on_value=set_combotype,
                values=["OR", "AND", "XOR"],
                classes=['variant="solo"'],
            )
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
    """Holds list of created virtual columns with deletes"""
    sl


@sl.component()
def VirtualColumnsPanel():
    df = State.df.value
    open, set_open = sl.use_state(False)
    expression, set_expression = sl.use_reactive("")
    name, set_name = sl.use_reactive("")
    error, set_error = sl.use_state("")

    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-calculator"])
            with rv.CardTitle(children=["Virtual calculations"]):
                pass
        with rv.ExpansionPanelContent():
            VirtualColumnList()
            btn = sl.Button(label="Add virtual column",
                            on_click=lambda: set_open(True))

    @task
    def validate():
        "Ensure syntax is correct"
        try:
            if expression == "":
                return None
            df.validate_expression(expression)

            # all good
            assert name not in df.get_column_names(virtual=True)

            # add virtual column
            close()
            return True

        except Exception as e:  # noqa
            # any exception, exit and report
            set_error(str(e))
            return False

    def close():
        """Clears state variables and closes dialog."""
        set_open(False)
        set_name("")
        set_expression("")

    with Dialog(
            open,
            title="Add virtual column",
            on_cancel=close,
            ok="Add",
            close_on_ok=False,
            on_ok=validate,
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
        if result.finished:
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


@sl.component()
def sidebar():
    df = State.df.value
    with sl.Sidebar():
        if df is not None:
            SumCard()
            with rv.ExpansionPanels(accordion=True):
                ExprEditor()
                QuickFilterMenu()
                CartonMapperPanel()
                # PivotTablePanel()
                # DownloadMenu()
        else:
            sl.Info("No data loaded.")
