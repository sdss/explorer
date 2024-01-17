import re
from functools import reduce
import operator

import solara as sl
import numpy as np
import reacton.ipyvuetify as rv

from solara.components.columns import Columns
from solara.components.card import Card
from solara.components.file_drop import FileDrop

from state import State, PlotState
from editor import ExprEditor, SumCard


@sl.component()
def dataset_menu():
    df = State.df.value
    with sl.Row():
        sl.Button(
            "Sample APOGEENET Dataset",
            color="primary",
            text=True,
            outlined=True,
            on_click=State.load_sample,
            disabled=df is not None,
        )
        sl.Button(
            "Clear dataset",
            color="primary",
            text=True,
            outlined=True,
            on_click=State.reset,
        )
    if df is None:
        FileDrop(
            on_file=State.load_from_file,
            on_total_progress=lambda *args: None,
            label="Drag file here",
        )


@sl.component()
def control_menu():
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
        # summary + expressions
        SumCard()
        ExprEditor()
        QuickFilterMenu()

        # pivot table
        sl.PivotTableCard(df, x=["telescope"], y=["release"])

        with sl.Row(style={"align-items": "center"}):
            sl.FileDownload(
                get_data,
                filename="apogeenet_filtered.csv",
                label="Download table",
            )
    else:
        sl.Info(
            "No data loaded, click on the sample dataset button to load a sample dataset, or upload a file."
        )


@sl.component()
def QuickFilterMenu():
    """
    Apply quick filters via check boxes.
    """
    df = State.df.value
    cols = df.get_column_names()
    flag_cols = []
    for col in cols:
        if re.search("flag", col):
            flag_cols.append(col)
    # TODO: find out how flags work, currently using 3 cols as plceholders:
    flag_cols = ["result_flags", "flag_bad", "flag_warn"]
    _filter, set_filter = sl.use_cross_filter(id(df), "quickflags")

    # Quick filter states
    flag_nonzero, set_flag_nonzero = sl.use_state(False)
    flag_snr50, set_flag_snr50 = sl.use_state(False)

    def work():
        # all false
        filters = []
        flags = [flag_nonzero, flag_snr50]
        if np.all(np.logical_not(flags)):
            set_filter(None)
            return
        # flag out all nonzero
        if flag_nonzero:
            for flag in flag_cols:
                # two types of flag
                print(f"({flag} == 0)")
                filters.append(df[f"({flag} == 0)"])
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

    with rv.Card(style_="height: 100%; width: 100%;") as main:
        with rv.ExpansionPanels(accordion=True):
            with rv.ExpansionPanel():
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
    return main


@sl.component()
def sidebar():
    with sl.Sidebar():
        with sl.Card("Controls", margin=0, elevation=0):
            with sl.Column():
                dataset_menu()
                control_menu()
