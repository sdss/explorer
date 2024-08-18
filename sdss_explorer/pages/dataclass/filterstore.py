"""Subsets filtering backend, containing all hooks/callback functions for subset functionality."""

import operator
from functools import reduce
from typing import Any, Union, Callable, Dict, List, TypeVar

import solara.util
from solara.hooks.misc import use_force_update, use_unique_key

T = TypeVar("T")

__all__ = [
    "use_subset",
]


class SubsetStore:

    def __init__(self) -> None:
        self.listeners: Dict[Any, List[Callable]] = {}
        # data_key (ID) : subset (str: name) : filter_key (unique str) : filter
        # 3 layer dictionary
        self.filters: Dict[Any, Dict[str, Any]] = {}

    def add(self, subset_key, key, filter):
        data_subset_filters = self.filters.setdefault(subset_key, {})
        data_subset_filters[key] = filter

    def use(self, subset_key, key, write_only: bool, eq=None):
        # we use this state to trigger update, we could do without

        data_subset_filters = self.filters.setdefault(subset_key, {})

        updater = use_force_update()

        # will update the filter if the subset changes
        filter, set_filter = solara.use_state(data_subset_filters.get(key),
                                              eq=eq)

        def on_change():
            set_filter(data_subset_filters.get(key))
            # even if we don't change our own filter, the other may change
            updater()

        def connect():
            self.listeners.setdefault(subset_key, []).append(on_change)
            # we need to force an extra render after the first render
            # to make sure we have the correct filter, since others components
            # may set a filter after we have rendered, *or* mounted
            on_change()

            def cleanup():
                self.listeners.setdefault(subset_key, []).remove(on_change)
                # also remove our filter, and notify the rest
                data_subset_filters.pop(key,
                                        None)  # remove, ignoring key error
                for listener in self.listeners.setdefault(subset_key, []):
                    listener()

            return cleanup

        if not write_only:
            # NOTE: conditional hook
            solara.use_effect(connect, [subset_key, key])

        def setter(filter):
            data_subset_filters[key] = filter
            print(
                "N listeners for",
                subset_key,
                "is",
                len(self.listeners.setdefault(subset_key, [])),
            )
            print(self.listeners.setdefault(subset_key, []))
            for listener in self.listeners.setdefault(subset_key, []):
                listener()

        # only return the other filters if required.
        if not write_only:
            otherfilters = [
                filter for key_other, filter in data_subset_filters.items()
                if key != key_other and filter is not None
            ]
        else:
            otherfilters = None
        return filter, otherfilters, setter


subset_context = solara.create_context(SubsetStore())


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
    subset_store = solara.use_context(subset_context)
    _own_filter, otherfilters, set_filter = subset_store.use(
        subset_reactive.value, key, write_only=write_only, eq=eq)
    if write_only:
        cross_filter = None  # never update
    else:
        if otherfilters:
            cross_filter = reduce(reducer, otherfilters[1:], otherfilters[0])
        else:
            cross_filter = None
    return cross_filter, set_filter


def remove_subset(subset_key: str):
    # TODO: how to trigger state updates correctly? How to force it
    # so that when the subset is removed, it resets subset setting per
    # plot to the only one in it?
    pass
