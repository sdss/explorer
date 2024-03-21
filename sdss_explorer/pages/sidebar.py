import re
from functools import reduce
import operator

import solara as sl
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv

from .state import State
from .editor import ExprEditor, SumCard


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
def PivotTablePanel():
    df: vx.DataFrame = State.df.value
    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-table-plus"])
            with rv.CardTitle(children=["Pivot Table"]):
                pass
        with rv.ExpansionPanelContent():
            sl.Markdown("### currently bugged")
            # BUG: says the df is a dictionary when it isnt
            # sl.PivotTableCard(df, y=["telescope"], x=["release"])
    return main


@sl.component()
def sidebar():
    ds = State.dataset.value
    df = State.df.value
    with sl.Sidebar():
        if ds != "" and df is not None:
            SumCard()
            with rv.ExpansionPanels(accordion=True):
                ExprEditor()
                QuickFilterMenu()
                PivotTablePanel()
                DownloadMenu()
        else:
            sl.Info("No data loaded.")
