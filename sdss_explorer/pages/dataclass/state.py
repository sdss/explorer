"""Main application state variables"""

import logging
import os
import json
from typing import Optional, cast

import pandas as pd
import solara as sl
import vaex as vx

from .subsetstore import SubsetStore

logger = logging.getLogger("sdss_explorer")

# disable the vaex built-in logging (clogs on FileNotFounds et al)
if sl.server.settings.main.mode == "production":
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
    """Loader for files to ensure authorization/etc"""
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
        logger.debug("Exception on dataload encountered", e)
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
        self.mapping = sl.reactive(open_file("mappings.parquet"))
        self.datamodel = sl.reactive(load_datamodel())

        # these force load
        self._release = sl.reactive("dr19")
        self._datatype = sl.reactive("star")

        # adaptively rerendered
        self.df = sl.reactive(cast(vx.DataFrame, None))

        # user-binded instances
        # NOTE: this approach allows UUID + subsetstore to be read-only
        self._uuid = sl.reactive(sl.get_session_id())
        self._kernel_id = sl.reactive(sl.get_kernel_id())
        self._subset_store = sl.reactive(SubsetStore())

    def load_dataset(self,
                     release: Optional[str] = None,
                     datatype: Optional[str] = None) -> None:
        # use attributes if not manually overridden
        if not release:
            release = self.release
        if not datatype:
            datatype = self.datatype

        # start with standard open operation
        # TODO: redux version via envvar?
        df = open_file(
            f"{release}/explorerAll{datatype.capitalize()}-0.6.0.hdf5")

        if df is None:
            logger.debug(
                "no dataset loaded, ensure everything is setup (files, envvars)"
            )
            return

        # shuffle to ensure skyplot looks nice, constant seed for reproducibility
        # df = df.shuffle(random_state=42)

        # create inaccessible indices column for target flags filtering

        # force materialization of target_flags column to maximize the performance
        # NOTE: embedded in a worker process, we will eat up significant memory with this command
        #  this is because all workers will materialize the column
        # TODO: to minimize this, we could add --preload option to solara or FastAPI runner, so that it forks the workers from the base instance.
        # NOTE: vaex has an add_column method, but as stated above, it will overload our worker process.
        #  for more info, see: https://vaex.io/docs/guides/performance.html
        df = df.materialize()

        self.df.set(df)

        return

    @property
    def release(self):
        return str(self._release.value)

    @property
    def datatype(self):
        return str(self._datatype.value)

    @property
    def uuid(self):
        return str(self._uuid.value)

    @property
    def kernel_id(self):
        return str(self._kernel_id.value)

    @property
    def subset_store(self):
        return self._subset_store.value

    def __repr__(self) -> str:
        """Show relevant properties of class as string"""
        return "\n".join(
            f"{k:15}: {v}" for k, v in {
                "uuid": self.uuid,
                "kernel_id": self.kernel_id,
                "df": hex(id(self.df.value)),
                "subset_backend": hex(id(self.subset_store)),
                "release": self.release,
                "datatype": self.datatype,
            }.items())


State = StateData()
