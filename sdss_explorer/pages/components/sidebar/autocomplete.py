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
    """Single selectable autocomplete"""
    pass


@sl.component_vue(vue_path="./autocompleteselect.vue")
def AutocompleteSelect(
    label: str,
    value: list[Any],
    on_value: Callable,
    values: list[Any],
    multiple: bool = True,
):
    pass
