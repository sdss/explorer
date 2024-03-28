from functools import reduce
from timeit import default_timer as timer
import operator

import solara as sl
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv

from .state import State
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

    # INFO: full reset on dataset change
    sl.use_thread(reset_filters, dependencies=[State.dataset.value])

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
    # flags, set_flags = sl.use_state(cast(TargetingFlags, None))
    flipflop = sl.use_reactive(
        False)  # NOTE: stupid workaround for no boolean indexing
    mapper, set_mapper = sl.use_state([])
    carton, set_carton = sl.use_state([])
    dataset, set_dataset = sl.use_state([])
    combotype, set_combotype = sl.use_state("OR")

    if filter:
        dff = df[filter]
    else:
        dff = df

    def update_filter():
        # convert chosens to bool mask
        mapping = State.mapping.value
        print("MapperCarton ::: starting filter update")
        print(mapper, carton)

        if len(mapper) == 0 and len(carton) == 0:
            print("No selections: empty exit case")
            set_filter(None)
            return

        start = timer()
        if combotype.lower() == "or":
            c = mapping["alt_name"].isin(carton)
            m = mapping["mapper"].isin(mapper)
            mask = c | m
            mask = mask.values
        elif combotype.lower() == "xor":
            c = mapping["alt_name"].isin(carton).values
            m = mapping["mapper"].isin(mapper).values
            mask = np.logical_xor(c, m)
        elif combotype.lower() == "and":
            c = mapping["alt_name"].isin(carton)
            m = mapping["mapper"].isin(mapper)
            mask = c & m
            mask = mask.values
        else:
            raise ValueError(
                "illegal combination type set for combining mapper/carton filter"
            )
        bits = np.arange(len(mapping))[mask]
        print("Timer for bit selection via mask:", round(timer() - start, 5))

        start = timer()
        # get flag_number & offset
        # NOTE: hardcoded nbits as 8, and nflags as 57
        num, offset = np.divmod(bits, 8)
        setbits = 57 > num  # ensure bits in flags

        # construct hashmap for each unique flag
        filters = np.zeros(57).astype("uint8")
        for unique in np.unique(num[setbits]):
            # ANDs all the bitshifted values for the given unique flag
            offsets = 1 << offset[setbits][np.where(num[setbits] == unique)]
            actives = reduce(operator.or_, offsets)  # INFO: must always be OR
            if actives == 0:
                continue  # skip
            filters[unique] = (
                actives  # the required active bit(s) ACTIVES for bitmask position "UNIQUE"
            )

        print("Timer for active mask creation:", round(timer() - start, 5))

        # generate a filter based on the vaex function defined above

        start = timer()
        cmp_filter = df.func.check_flags(df["sdss5_target_flags"], filters)
        print("Timer for expression generation:", round(timer() - start, 5))
        set_filter(cmp_filter)

        return

    sl.use_thread(update_filter,
                  dependencies=[mapper, carton, dataset, combotype])

    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-magnify-scan"])
            with rv.CardTitle(children=["Mapper, carton, cartons, dataset"]):
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
                # sl.SelectMultiple(
                #    label="Dataset",
                #    values=dataset,
                #    on_value=set_dataset,
                #    all_values=State.datasets,
                #    classes=['variant="solo"'],
                # )
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


@sl.component()
def sidebar():
    ds = State.dataset.value
    df = State.df.value
    with sl.Sidebar():
        if ds != "" and df is not None and type(df) != dict:
            SumCard()
            with rv.ExpansionPanels(accordion=True):
                ExprEditor()
                QuickFilterMenu()
                CartonMapperPanel()
                PivotTablePanel()
                DownloadMenu()
        else:
            sl.Info("No data loaded.")
