"""Generic autocomplete component"""
import solara as sl
from typing import Callable, Dict, List, Optional, TypeVar, Union, cast, overload
import reacton.ipyvuetify as rv
import vaex as vx
import numpy as np
from typing import List
import re

from itertools import permutations

from ...dataclass import Alert

T = TypeVar("T")


def gen_fuzzy_regex(input_string: str) -> str:
    """Generate a basic fuzzy finding regex pattern from a string.

    A string could be "a foo bar" and the pattern would become:
    ((a).*(foo).*(bar))|((a).*(bar).*(foo))|((foo).*(a).*(bar))|...

    :param input_string: the input string to generate the pattern from
    :return: the generated pattern as a string
    """
    words = input_string.split()
    words = filter(lambda x: len(x) > 0, words)
    word_permutations = permutations(words)
    patterns = []

    for perm in word_permutations:
        pattern_part = ".*".join(f"(?i)({word})" for word in perm)
        patterns.append(f"({pattern_part})")

    return "|".join(patterns)


def filter_components(df: vx.DataFrame | List, col: str, query: str):
    """Filter a dataframe or list by a column for a given query"""
    try:
        if len(query) == 0:
            return []
        # TODO: update with fuzzy search
        else:
            if isinstance(df, vx.DataFrame):
                return df[df[col].str.contains(
                    gen_fuzzy_regex(query), regex=True)][col].values.tolist()
            # regex a list
            elif isinstance(df, list):
                return list(
                    filter(re.compile(gen_fuzzy_regex(query)).search, df))
    except Exception:
        Alert.update(
            message=
            'Filter on autocomplete crashed! If persistent, please inform server admins.',
            color='error')
        return []
    return


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

    def input_hook(*args: str) -> None:
        """Input field hook to update preview data."""
        query = args[-1]
        set_components(filter_components(df=df, col=expr, query=query))

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
                       **kwargs):
    """Selectable component to select an single from a given list. Mimics solara.Select API."""
    found_components, set_components = sl.use_state([])
    input, set_input = sl.use_state("")

    reactive_value = sl.use_reactive(value, on_value)  # type: ignore
    del value, on_value

    def input_hook(*args: str) -> None:
        """Input field hook to update preview data."""
        query = args[-1]
        set_components(
            list(filter(re.compile(gen_fuzzy_regex(query)).search, values)))

    # create the autocomplete component to select the component
    component = rv.Autocomplete(
        label=label,
        #filled=True,
        v_model=reactive_value.value,
        on_v_model=reactive_value.set,
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
