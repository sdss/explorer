"""Main application state variables"""

import logging
import os
import pathlib
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
    """Load the pre-compiled column JSON for a given dataset.

    Args:
        release: data release directory to for
        datatype: specific datatype of file to load. (`'star', 'visit'`)

    """
    # get dataset name
    datapath = settings.datapath

    # fail case for no envvar
    if datapath is None:
        return None

    file = f"{release}/columnsAll{datatype.capitalize()}-{VASTRA}.json"
    path = pathlib.Path(f"{datapath}/{file}")
    if not path.exists():
        logger.critical(
            "Expected to find %s for column lookup, didn't find it.", file)
        return None

    with open(path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        return data


def open_file(filename):
    """Vaex open wrapper for datafiles to ensure authorization/file finding.

    Args:
        filename (str): filename to open

    """
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
            "Expected to find %s for dataframe, didn't find it.", filename)
        return None
    except Exception as e:
        logger.debug("caught exception on dataframe load: %s", e)
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

    path = pathlib.Path(f"{settings.datapath}/{file}")
    if not path.exists():
        logger.critical(
            "Expected to find %s for column glossary datamodel, didn't find it.", path
        )
        return None

    try:
        with open(f"{settings.datapath}/{file}", "r", encoding='utf-8') as f:
            data = json.load(f).values()
    except Exception as e:
        logger.debug("caught exception on datamodel loader: %s", e)
        return None
    else:
        logger.info('successfully loaded datamodel')
        return pd.DataFrame(data)  # TODO: back to vaex



class StateData:
    """Holds app-wide state variables

    Attributes:
        mapping (solara.Reactive[vx.DataFrame]): bitmappings dataframe, used for targeting filters.
        datamodel (solara.Reactive[pd.DataFrame]): column glossary dataframe

        df (solara.Reactive[vx.DataFrame]): loaded dataframe file, defaults to nothing but app will instantiate with one loaded.
        columns (solara.Reactive[dict[str,list[str]]]): column lookup, used for guardrailing.

        release (str): release type
        datatype (str): datatype of file
    """

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
        """ load the HDF5 dataset for the dashboard """
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
    def release(self) -> str:
        """Current release of app (dr19, etc)"""
        return str(self._release.value)

    @property
    def datatype(self) -> str:
        """Current datatype of app (star or visit)"""
        return str(self._datatype.value)

    def get_default_dataset(self) -> str:
        """Method version to get the default dataset of app (star or visit). Used for defaulting the Subset dataclass"""
        datatype = self._datatype.value
        return "mwmlite" if datatype == "star" else "thepayne"

    @property
    def uuid(self) -> str:
        """User ID; Solara Session ID"""
        return str(self._uuid.value)

    @property
    def kernel_id(self) -> str:
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
"""Specific StateData instance used for app"""
