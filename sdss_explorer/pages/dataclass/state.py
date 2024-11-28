"""Main application state variables"""

import os
import json

import pandas as pd
import solara as sl
import vaex as vx

from .subsetstore import SubsetStore
from ..util import _datapath, open_file

# disable the vaex built-in logging (clogs on FileNotFounds et al)
if sl.server.settings.main.mode == 'production':
    vx.logging.remove_handler()  # force remove handler on production instance


def load_datamodel() -> pd.DataFrame | None:
    """Loader for datamodel"""
    # TODO: replace with a real datamodel from the real things
    # TODO: revert loader back to previous version
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

        # adaptively rerendered
        self.release = sl.reactive('dr19')
        #self.df = sl.reactive(StateData.load_dataset(self.dataset.value))
        #self.columns = sl.reactive(self.df.value.get_column_names() if self.df.
        #                           value is not None else None)

        # user-binded instances
        # NOTE: this approach allows UUID + subsetstore to be read-only
        self._uuid = sl.reactive(sl.get_session_id())
        self._subset_store = sl.reactive(SubsetStore())

    def __repr__(self) -> str:
        return str({
            'uuid': self.uuid,
            #'df': hex(id(self.df.value)),
            'release': self.release.value,
            'subset_backend': self.subset_store,
        })

    @property
    def uuid(self):
        return str(self._uuid.value)

    @property
    def subset_store(self):
        return self._subset_store.value

    def initialize(self):
        """Initializes with session-lockgrid_stateed parameters"""
        # memoize it all
        uuid = sl.use_memo(sl.get_session_id, [])
        subset_store = sl.use_memo(SubsetStore, [])

        # set values to memoized results
        self._uuid.value = uuid
        self._subset_store.value = subset_store

        # return memoized values to component so they exist
        return (uuid, subset_store)

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]


State = StateData()
