"""Main application state variables"""

from typing import cast, Any, List, Dict, Callable
import os
import json

import solara as sl
import vaex as vx
import numpy as np

from .gridstate import GridData

from ..util import generate_unique_key
from solara.hooks.misc import use_force_update

# disable the vaex built-in logging (clogs on FileNotFounds et al)
if sl.server.settings.main.mode == 'production':
    vx.logging.remove_handler()  # force remove handler on production instance


def _datapath():
    """fetches path to parquet files from envvar"""
    datapath = os.getenv(
        "EXPLORER_DATAPATH"
    )  # NOTE: does not expect a slash at end of the envvar, can account for it in future
    if datapath:
        return datapath
    else:
        return None


def open_file(filename):
    """Loader for files to catch excepts"""
    # get dataset name
    datapath = _datapath()

    # fail case for no envvar
    if datapath is None:
        return None

    # TODO: verify auth status when attempting to load a working group dataset

    # fail case for no file found
    try:
        dataset = vx.open(f"{datapath}/{filename}")
        return dataset
    except Exception as e:  # noqa
        print('Exception on dataload encountered', e)
        # NOTE: this should deal with exception quietly; can be changed later if desired
        return None


def load_datamodel() -> vx.DataFrame | None:
    """Loader for datamodel"""
    # TODO: replace with a real datamodel from the real things
    datapath = _datapath()
    print('LOADING DATAMODEL ASJDIFJIJ')
    # no datapath
    if datapath is None:
        return None

    # no fail found
    try:
        with open(f"{_datapath()}/ipl3_partial.json") as f:
            data = json.load(f).values()
            f.close()
        return vx.DataFrame(data)
    except Exception:
        return None


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
        sl.use_effect(connect, [subset_key, key])

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


class StateData:
    """Holds app-wide state variables"""

    def __init__(self):
        self.mapping = sl.reactive(open_file('mappings.parquet'))
        self.datamodel = sl.reactive(cast(vx.DataFrame, None))

        # NOTE: this forces UUID + subsetstore to be read-only
        self._uuid = sl.reactive(sl.get_session_id())
        self._subset_store = sl.reactive(SubsetStore())
        self._grid_state = sl.reactive(GridData())

        # TODO: set to read from cookie on first load
        self.dataset = sl.reactive('ipl3_partial')
        self.df = sl.reactive(StateData.load_dataset(self.dataset.value))
        self.columns = sl.reactive(self.df.value.get_column_names() if self.df.
                                   value is not None else None)

        # initializing app with a simple default to demonstrate functionality

    def __repr__(self) -> str:
        return str('state')

    @property
    def uuid(self):
        return str(self._uuid.value)

    @property
    def subset_store(self):
        return self._subset_store.value

    @property
    def grid_state(self):
        return self._grid_state.value

    @staticmethod
    def load_dataset(dataset):
        # start with standard open operation
        df = open_file(f'{dataset}.parquet')

        if df is None:
            print('no dataset loaded')
            return

        # force cast flags as a numpy array via my method bypassing pyarrow
        flags = np.array(list(
            df["sdss5_target_flags"].values.to_numpy())).astype("uint8")
        df["sdss5_target_flags"] = flags

        # shuffle to ensure skyplot looks nice, constant seed for reproducibility
        df = df.shuffle(random_state=42)

        # force materialization of target_flags column to maximize the performance
        # NOTE: embedded in a worker process, we will eat up significant memory with this command
        #  this is because all workers will materialize the column
        # TODO: to minimize this, we could add --preload option to solara or FastAPI runner, so that it forks the workers from the base instance.
        # NOTE: vaex has an add_column method, but as stated above, it will overload our worker process.
        #  for more info, see: https://vaex.io/docs/guides/performance.html
        df = df.materialize()

        return df

    def initialize(self):
        """Initializes with session-locked parameters"""
        uuid = sl.use_memo(sl.get_session_id, [])
        subset_store = sl.use_memo(SubsetStore, [])
        grid_state = sl.use_memo(GridData, [])
        State._uuid.value = uuid
        State._subset_store.value = subset_store
        State._grid_state.value = grid_state
        return (uuid, subset_store, grid_state)

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]


State = StateData()
