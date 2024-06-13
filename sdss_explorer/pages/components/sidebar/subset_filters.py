"""Holds specific filter components"""

from functools import reduce
import operator

import solara as sl
import numpy as np
import reacton.ipyvuetify as rv

from ...dataclass import State, use_subset, Alert

__all__ = [
    "ExprEditor", "CartonMapperPanel", "QuickFilterMenu", "PivotTablePanel"
]


@sl.component()
def ExprEditor(expression, set_expression, error, result):
    """Expression editor user-facing set"""
    # expression editor
    with sl.Column(gap="0px") as main:
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
    return main


@sl.component()
def CartonMapperPanel(mapper, set_mapper, carton, set_carton, dataset,
                      set_dataset):
    with rv.ExpansionPanel() as main:
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
                            # TODO: fetch via valis or via df itself
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
    return main


@sl.component()
def QuickFilterMenu(name):
    """
    Apply quick filters via check boxes. Deprecated, to be implemented again in future.
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
    """Holds solara PivotTable in expansion panel. Deprecated (maybe implement again in future)"""
    df = State.df.value
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
def DownloadMenu():
    # df = State.df.value
    # filter, set_filter = sl.use_cross_filter(id(df), "download")
    # if filter:
    #    dff = df[filter]
    # else:
    #    dff = df

    def get_data():
        # TODO: change all of these methods to better valis-integrated methods that dont involve
        # dropping the entire DB file into memory...
        # dfp = dff.to_pandas_df()
        Alert.update(
            "Download currently unsupported due to memory issues server-side. Coming soon!",
            color="info",
        )
        return  # dfp.to_csv(index=False)

    with sl.Tooltip("Download subset as csv") as main:
        sl.Button(
            label="",
            icon_name="mdi-download",
            icon=True,
            text=True,
            on_click=get_data,
            # NOTE: temporary disable because the interface is poor
        )

    return main
