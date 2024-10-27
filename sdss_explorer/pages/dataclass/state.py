"""Main application state variables"""

import os
import json

import pandas as pd
import solara as sl
import vaex as vx
import numpy as np

from .subsetstore import SubsetStore

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


def load_datamodel() -> pd.DataFrame | None:
    """Loader for datamodel"""
    # TODO: replace with a real datamodel from the real things
    datapath = _datapath()
    # no datapath
    if datapath is None:
        return None

    # no fail found
    try:
        with open(f"{_datapath()}/ipl3_partial.json") as f:
            data = json.load(f).values()
            f.close()
        return pd.DataFrame(data)
    except Exception:
        return None


class StateData:
    """Holds app-wide state variables"""

    def __init__(self):
        # global, read-only reactives, dont care
        self.mapping = sl.reactive(open_file('mappings.parquet'))
        self.datamodel = sl.reactive(load_datamodel())
        self.dataset = sl.reactive(
            'ipl3_partial')  # TODO: set to read from cookie on first load

        # adaptively rerendered
        self.df = sl.reactive(StateData.load_dataset(self.dataset.value))
        self.columns = sl.reactive(self.df.value.get_column_names() if self.df.
                                   value is not None else None)

        # user-binded instances
        # NOTE: this approach allows UUID + subsetstore to be read-only
        self._uuid = sl.reactive(sl.get_session_id())
        self._subset_store = sl.reactive(SubsetStore())

    def __repr__(self) -> str:
        return str({
            'uuid': self.uuid,
            'df': hex(id(self.df.value)),
            'dataset': self.dataset.value,
            'subset_backend': self.subset_store,
        })

    @property
    def uuid(self):
        return str(self._uuid.value)

    @property
    def subset_store(self):
        return self._subset_store.value

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
        """Initializes with session-lockgrid_stateed parameters"""
        # memoize it all
        df = sl.use_memo(
            lambda *args: StateData.load_dataset(self.dataset.value),
            dependencies=[self.dataset.value])
        uuid = sl.use_memo(sl.get_session_id, [])
        subset_store = sl.use_memo(SubsetStore, [])

        # set values to memoized results
        self._uuid.value = uuid
        self._subset_store.value = subset_store
        self.df.value = df

        # return memoized values to component so they exist
        return (uuid, subset_store, df)

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]


State = StateData()
