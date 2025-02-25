"""App-facing subset filters and expression storage dataclass"""

from typing import Any, List, Dict, Callable
import collections.abc

import solara as sl

from solara.hooks.misc import use_force_update


class SubsetStore:

    def __init__(self) -> None:
        self.listeners: Dict[Any, List[Callable]] = {}
        # data_key (ID) : subset (str: name) : filter_key (unique str) : filter
        # 3 layer dictionary
        self.filters: Dict[Any, Dict[str, Dict[str, Any]]] = {}

    def add(self, data_key, subset_key, key, filter):
        data_subset_filters = self.filters.setdefault(data_key, {}).setdefault(
            subset_key, {})
        data_subset_filters[key] = filter

    def use(self, data_key, subset_key, key, write_only: bool, eq=None):
        # we use this state to trigger update, we could do without

        data_subset_filters = self.filters.setdefault(data_key, {}).setdefault(
            subset_key, {})

        updater = use_force_update()

        # will update the filter if the subset changes
        filter, set_filter = sl.use_state(data_subset_filters.get(key), eq=eq)

        def on_change():
            set_filter(data_subset_filters.get(key))
            # even if we don't change our own filter, the other may change
            updater()

        def connect():
            # dont save ourself
            if not write_only:
                self.listeners.setdefault(subset_key, []).append(on_change)
            # we need to force an extra render after the first render
            # to make sure we have the correct filter, since others components
            # may set a filter after we have rendered, *or* mounted
            on_change()

            def cleanup():
                # dont save ourself
                if not write_only:
                    self.listeners.setdefault(subset_key, []).remove(on_change)
                # also remove our filter, and notify the rest
                data_subset_filters.pop(key,
                                        None)  # remove, ignoring key error

                for listener in self.listeners.setdefault(subset_key, []):
                    listener()

            return cleanup

        # BUG: removing this hook prevents cleanup BETWEEN virtual kernels (somehow?), so we need this to stay
        sl.use_effect(connect, [subset_key, key, data_key])

        def setter(filter):
            data_subset_filters[key] = filter
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

    @staticmethod
    def map_expressions(d):
        if isinstance(d, collections.abc.Mapping):
            return {k: SubsetStore.map_expressions(v) for k, v in d.items()}
        else:
            return d._expression

    def __repr__(self) -> str:
        return str({
            'listeners': self.listeners,
            'filters': SubsetStore.map_expressions(self.filters),
        })
