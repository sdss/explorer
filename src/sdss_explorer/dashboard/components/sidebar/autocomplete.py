"""Autocomplete components"""

import solara as sl
from typing import Any, Callable


@sl.component_vue(vue_path="./autocompletesingle.vue")
def SingleAutocomplete(
    label: str,
    value: Any,
    on_value: Callable,
    values: list[Any],
    disabled: bool = False,
    allow_none: bool = False,
):
    """Autocomplete component with single selection

    Note:
        this is a vue component. Look at the relevant vue file.

    Args:
        label: component text label
        value: selected thing value
        on_value: value setter for `value`
        values: list of values that are selectable
        disabled: whether disabled; prop is synced live
        allow_none: can value be set to None?


    """
    pass


@sl.component_vue(vue_path="./autocompleteselect.vue")
def AutocompleteSelect(
    label: str,
    value: list[Any],
    on_value: Callable,
    values: list[Any],
    multiple: bool = True,
):
    """Autocomplete component via selection

    Note:
        this is a vue component. Look at the relevant vue file.

    Args:
        label: component text label
        value: value of selectables
        on_value: value setter for `value`
        values: list of values that are selectable
        multiple: allow multiple selections
    """

    pass
