"""Subsets filtering backend, containing all hooks/callback functions for subset functionality."""

import operator
from functools import reduce
from typing import Callable, TypeVar, Union

import solara.util
from solara.hooks.misc import use_unique_key

from .state import State

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


    Args:
        data_key (int): expected id(DataFrame)
        subset_key: the key for the subset. Can be reactive or string.
        name: name of the reducer, used to help identify in debugs
        write_only: whether this filter should attach a listener. Can significantly increase performance with many filters.
        reducer: type of reduction to use on the returned cross filtering.
        eq (Callable[[Any,Any],bool]): type of equality check to use

    Returns:
        cross_filter (vx.Expression): combined crossfilter
        set_filter (Callable): callable method to set a filter
    """
    subset_reactive = solara.use_reactive(subset_key)
    del subset_key

    key = use_unique_key(prefix=f"ss-{name}-")
    subset_store = State.subset_store  # solara.use_context(subset_context)
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
