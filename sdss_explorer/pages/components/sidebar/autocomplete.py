"""Generic autocomplete component"""
import solara as sl
from typing import List, TypeVar
import reacton.ipyvuetify as rv
import vaex as vx

T = TypeVar("T")


def AutocompleteSelect(filter,
                       set_filter,
                       df: vx.DataFrame | List,
                       expr: str,
                       field: str,
                       multiple: bool = False,
                       **kwargs):
    """Selectable component to select an option or multiple options from a given list."""
    found_components, set_components = sl.use_state([])
    all = list(df[expr].unique()) if isinstance(df, vx.DataFrame) else df
    input, set_input = sl.use_state("")

    # create the autocomplete component to select the component
    component = rv.Autocomplete(
        label=field,
        #filled=True,
        v_model=filter,
        on_v_model=set_filter,
        items=all,
        style={"width": "100%"},
        chips=multiple,  # show with chips if multiple
        small_chips=multiple,
        hide_selected=True,
        multiple=multiple,
        deletable_chips=multiple,
        auto_select_first=True,
        validate_on_blur=True,
        value=input,
        filled=True,
        no_data_text=f"No matching {field}s found",
        **kwargs,
    )
    rv.use_event(component, 'blur', lambda *_: set_input(''))
    rv.use_event(component, 'keyup:enter', lambda *_: set_input(''))
    #rv.use_event(component, 'keydown.esc', )
    #rv.use_event(component, "update:search-input", input_hook)

    return component


def SingleAutocomplete(label: str,
                       values: List[T],
                       value=None,
                       on_value=None,
                       allow_none: bool = False,
                       **kwargs):
    """Selectable component to select an single from a given list. Mimics solara.Select API."""
    input, set_input = sl.use_state("")

    def setting_parser(vmodel_data):
        """Parses vmodel data to disallow a None"""
        if vmodel_data or allow_none:
            reactive_value.set(vmodel_data)
        return

    reactive_value = sl.use_reactive(value, on_value)  # type: ignore
    del value, on_value

    # create the autocomplete component to select the component
    component = rv.Autocomplete(
        label=label,
        #filled=True,
        v_model=reactive_value.value,
        on_v_model=setting_parser,
        items=values,
        style={"width": "100%"},
        hide_selected=True,
        auto_select_first=True,
        validate_on_blur=True,
        value=input,
        filled=True,
        # TODO: fix how this looks in the plot settings
        no_data_text=f"No matching {label}s found",
        **kwargs,
    )

    return component
