"""Main application state variables"""

import logging
import os
import json
from typing import Optional, cast

import pandas as pd
import solara as sl
import vaex as vx

from .subsetstore import SubsetStore
from ...util import settings

logger = logging.getLogger("dashboard")

# disable the vaex built-in logging (clogs on FileNotFounds et al)
if sl.server.settings.main.mode == "production":
    vx.logging.remove_handler()  # force remove handler on production instance

VASTRA = settings.vastra
DATAPATH = settings.datapath

if DATAPATH is None:
    logger.critical("Datapath envvar is not set! App cannot function.")


def load_column_json(release: str, datatype: str) -> dict | None:
    """Load the pre-compiled column JSON for a given dataset."""
    # get dataset name
    datapath = settings.datapath

    # fail case for no envvar
    if datapath is None:
        return None

    file = f"{release}/columnsAll{datatype.capitalize()}-{VASTRA}.json"

    try:
        with open(f"{datapath}/{file}") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = None
        logger.critical(
            f"Expected to find {file} for column lookup, didn't find it.")
    return data


def open_file(filename):
    """Vaex open wrapper for datafiles to ensure authorization/file finding."""
    # get dataset name
    datapath = settings.datapath

    # fail case for no envvar
    if datapath is None:
        return None

    # TODO: verify auth status when attempting to load a working group dataset
    try:
        dataset = vx.open(f"{datapath}/{filename}")
        dataset = dataset.shuffle(
            random_state=42
        )  # shuffle to ensure skyplot looks nice, constant seed for reproducibility
        return dataset
    except FileNotFoundError:
        logger.critical(
            f"Expected to find {filename} for dataframe, didn't find it.")
        return None
    except Exception as e:
        logger.debug(f"caught exception on dataframe load: {e}")
        return None


def load_datamodel() -> pd.DataFrame | None:
    """Loads a given compiled datamodel, used in conjunction with the column glossary"""
    datapath = settings.datapath
    # no datapath
    if datapath is None:
        return None

    # no fail found
    # TODO: replace with a real datamodel from the real things
    file = "ipl3_partial.json"
    try:
        with open(f"{settings.datapath}/{file}") as f:
            data = json.load(f).values()
            f.close()
        return pd.DataFrame(data)  # TODO: back to vaex
    except FileNotFoundError as e:
        logger.critical(
            f"Expected to find {file} for column glossary datamodel, didn't find it: {e}"
        )
    except Exception as e:
        logger.debug(f"caught exception on datamodel loader: {e}")
        return None


class StateData:
    """Holds app-wide state variables"""

    def __init__(self):
        # globally shared, read only files
        self.mapping = sl.reactive(
            open_file("mappings.parquet"))  # mappings for bitmasks
        self.datamodel = sl.reactive(load_datamodel())  # datamodel spec

        # app settings, underscored to hide prop
        self._release = sl.reactive(cast(str, None))  # TODO: dr19
        self._datatype = sl.reactive(cast(str, None))

        # adaptively rerendered on changes; set on startup in app root
        self.df = sl.reactive(cast(vx.DataFrame, None))  # main datafile
        self.columns = sl.reactive(cast(
            dict, None))  # column glossary for guardrailing

        # user-binded instances
        # NOTE: this approach allows UUID + subsetstore to be read-only
        self._uuid = sl.reactive(sl.get_session_id())
        self._kernel_id = sl.reactive(sl.get_kernel_id())
        self._subset_store = sl.reactive(SubsetStore())

    def load_dataset(self,
                     release: Optional[str] = None,
                     datatype: Optional[str] = None) -> bool:
        # use attributes if not manually overridden
        if not release:
            release = self.release
        if not datatype:
            datatype = self.datatype

        # start with standard open operation
        # TODO: redux version via envvar?
        df = open_file(
            f"{release}/explorerAll{datatype.capitalize()}-{VASTRA}.hdf5")
        columns = load_column_json(release, datatype)

        if (df is None) and (columns is None):
            logger.critical(
                "Part of dataset load failed! ensure everything is setup (files, envvars)"
            )
            return False

        # set reactives
        self.df.set(df)
        self.columns.set(columns)

        return True

    @property
    def release(self):
        """Current release of app (dr19, etc)"""
        return str(self._release.value)

    @property
    def datatype(self):
        """Current datatype of app (star or visit)"""
        return str(self._datatype.value)

    @property
    def uuid(self):
        """User ID; Solara Session ID"""
        return str(self._uuid.value)

    @property
    def kernel_id(self):
        """Virtual kernel ID"""
        return str(self._kernel_id.value)

    @property
    def subset_store(self):
        """Internal subset backend"""
        return self._subset_store.value

    def __repr__(self) -> str:
        """Show relevant properties of class as string."""
        return "\n".join(
            f"{k:15}: {v}" for k, v in {
                "uuid": self.uuid,
                "kernel_id": self.kernel_id,
                "df": hex(id(self.df.value)),  # dataframe mem address
                "subset_backend": hex(id(self.subset_store)),
                "release": self.release,
                "datatype": self.datatype,
            }.items())


State = StateData()
