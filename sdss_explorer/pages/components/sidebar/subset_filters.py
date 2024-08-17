"""Holds specific filter components"""

from functools import reduce
import operator

import solara as sl
import reacton.ipyvuetify as rv

from ...dataclass import State, use_subset, Alert
from .autocomplete import AutocompleteSelect, SingleAutocomplete
from .glossary import Help
from ..textfield import InputTextExposed

__all__ = [
    "ExprEditor", "TargetingFiltersPanel", "QuickFilterMenu",
    "PivotTablePanel", "DatasetSelect"
]


@sl.component()
def ExprEditor(expression, set_expression, error, result):
    """Expression editor user-facing set"""
    open, set_open = sl.use_state(False)
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
def DatasetSelect(dataset, set_dataset):
    """Select box for pipeline."""
    return SingleAutocomplete(
        label='Dataset',
        # TODO: fetch via valis or via df.row.unique()
        values=['apogeenet', 'thecannon', 'aspcap'],
        value=dataset,
        on_value=set_dataset)


@sl.component()
def TargetingFiltersPanel(mapper, set_mapper, carton, set_carton, flags,
                          set_flags):
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
                    AutocompleteSelect(
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

        concat_filter = reduce(operator.and_, filters[1:], filters[0])
        set_filter(concat_filter)
        return

    # apply thread to filtering logic so it only runs on rerenders
    sl.use_thread(work, dependencies=[flags])
    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-table-plus"])
            with rv.CardTitle(children=["Quick Flags"]):
                pass
        with rv.ExpansionPanelContent():
            pass

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
