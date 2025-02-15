"""Autocomplete components"""

import solara as sl
from typing import Any, Callable, List, TypeVar
import reacton.ipyvuetify as rv
import vaex as vx

T = TypeVar("T")


def SingleAutocomplete(
    label: str,
    values: List[T],
    value=None,
    on_value=None,
    allow_none: bool = False,
    **kwargs,
):
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
        # filled=True,
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


@sl.component_vue(vue_path="./autocompleteselect.vue")
def AutocompleteSelect(
    label: str,
    value: list[Any],
    on_value: Callable,
    values: list[Any],
    multiple: bool = True,
):
    pass
