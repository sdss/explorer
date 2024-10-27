"""Subsets filtering backend, containing all hooks/callback functions for subset functionality."""

import operator
from functools import reduce
from typing import Any, Union, Callable, Dict, List, TypeVar

import solara.util
from solara.hooks.misc import use_force_update, use_unique_key

from sdss_explorer.pages.dataclass.state import State

T = TypeVar("T")

__all__ = ["use_subset"]


def use_subset(
    data_key,
    subset_key: Union[solara.Reactive[str], str] = "A",
    name: str = "no-name",
    write_only: bool = False,
    reducer: Callable[[T, T], T] = operator.and_,
    eq=solara.util.numpy_equals,
):
    """Provides cross filtering across a subset, all other filters are combined using the reducer.

    Cross filtering will collect a set of filters (from other components), and combine
    them into a single filter, that excludes the filter we set for the current component.
    This is often used in dashboards where a filter is defined in a visualization component,
    but only applied to all other components.

    The graph below shows what happens when component A and B set a filter, and C does not.

    ```mermaid
    graph TD;
        A--"filter A"-->B;
        B--"filter B"-->C;
        A--"filter A"-->C;
        B--"filter B"-->A;
    ```
    """
    subset_reactive = solara.use_reactive(subset_key)
    del subset_key

    key = use_unique_key(prefix=f"ss-{name}-")
    subset_store = State.subset_store  #solara.use_context(subset_context)
    _own_filter, otherfilters, set_filter = subset_store.use(
        str(data_key),
        subset_reactive.value,
        key,
        write_only=write_only,
        eq=eq)
    if write_only:
        cross_filter = None  # never update
    else:
        if otherfilters:
            cross_filter = reduce(reducer, otherfilters[1:], otherfilters[0])
        else:
            cross_filter = None
    return cross_filter, set_filter
