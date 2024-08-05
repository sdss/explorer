"""Holds specific filter components"""

from functools import reduce
import operator

import solara as sl
import numpy as np
import reacton.ipyvuetify as rv

from ...dataclass import State, use_subset, Alert
from ..dialog import Dialog
from .autocomplete import AutocompleteSelect

__all__ = [
    "ExprEditor", "TargetingFiltersPanel", "QuickFilterMenu", "PivotTablePanel"
]

md_text = """_Expressions_ refer to columnar data-based filters you can apply onto the subset. The exact syntax uses generic, Python-like modifiers, similarly to the `pandas` DataFrame protocol. 

For example, you can enter:

    teff < 9e3 & logg > 2

to apply a filter for $T_{\mathrm{eff}} < 9000$ and $\log g > 2$ across the SDSS dataset.

Similarly, you can enter more advanced expressions like:

    (teff < 9e3 | teff > 12e3) & fe_h <= -2.1 & result_flags != 1
"""


@sl.component()
def ExpressionBlurb():
    """Simple markdown-based blurb for expression syntax."""
    open, set_open = sl.use_state(False)

    with sl.Tooltip("About expression syntax") as main:
        with sl.Button(
                icon=True,
                icon_name="mdi-information-outline",
                on_click=lambda: set_open(True),
                style={
                    "align": "center",
                    "justify": "center"
                },
        ):
            with Dialog(
                    open,
                    ok=None,
                    title="About Expressions",
                    cancel="close",
                    on_cancel=lambda: set_open(False),
            ):
                with rv.Card(flat=True, style_="width: 100%; height: 100%"):
                    sl.Markdown(md_text)

    return main


@sl.component()
def ExprEditor(expression, set_expression, error, result):
    """Expression editor user-facing set"""
    # expression editor
    with sl.Column(gap="0px") as main:
        with sl.Row(justify='center', style={"align-items": "center"}):
            sl.InputText(
                label="Enter an expression",
                value=expression,
                on_value=set_expression,
            )
            ExpressionBlurb()
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
def TargetingFiltersPanel(mapper, set_mapper, carton, set_carton, dataset,
                      set_dataset,flags, set_flags):
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
                    AutocompleteSelect(
                        flags,
                        set_flags,
                        clearable=True,
                        df=['SNR > 50', 'Only non-flagged', 'No bad flags'],expr='foobar',field='Quick Flags',multiple=True)
                    AutocompleteSelect(mapper,
                                       set_mapper,
                                       df=State.mapping.value,
                                       expr='mapper',
                                       field='Mapper',
                                       multiple=True)
                    AutocompleteSelect(dataset,
                                       set_dataset,
                                       # TODO: fetch via valis or via df.row.unique()
                                       df=['apogeenet', 'thecannon', 'aspcap'],
                                       expr='dataset',
                                       field='Dataset',
                                       multiple=True)
                    AutocompleteSelect(carton,
                                       set_carton,
                                       df=State.mapping.value,
                                       expr='alt_name',
                                       field='Carton',
                                       multiple=True)
    return main


@sl.component()
def QuickFilterMenu(name):
    """
    Apply Quick Filters
    """
    df = State.df.value
    # TODO: find out how flags work, currently using 1 col as plceholders:
    flag_cols = ["result_flags"]
    _filter, set_filter = use_subset(id(df),
                                     name,
                                     "quickflags",
                                     write_only=True)

    # Quick filter states
    flags, set_flags = sl.use_state(["SNR > 50"])

    def reset_filters():
        set_flags([])

    def work():
        filters = []
        if "SNR > 50" in flags:

        concat_filter = reduce(operator.and_, filters[1:], filters[0])
        set_filter(concat_filter)
        return

    # apply thread to filtering logic so it only runs on rerenders
    sl.use_thread(
        work,
        dependencies=[flags]
    )
    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-table-plus"])
            with rv.CardTitle(children=["Quick Flags"]):
                pass
        with rv.ExpansionPanelContent():

            #with rv.Card() as main:
            #    with rv.CardTitle(children=["Quick filters"]):
            #        rv.Icon(children=["mdi-filter-plus-outline"])
            #    with rv.CardText():
            #        sl.Checkbox(
            #            label="All flags zero",
            #            value=flag_nonzero,
            #            on_value=set_flag_nonzero,
            #        )
            #        sl.Checkbox(label="SNR > 50",
            #                    value=flag_snr50,
            #                    on_value=set_flag_snr50)
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
            if not isinstance(df, dict):
                # BUG: says the df is a dictionary when it isnt, no idea why this occurs
                # NOTE: the fix below fixes it, but is weird
                if type(df) != dict:  # noqa
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
