"""Main application state variables"""

import os
import json

import solara as sl
import pandas as pd
import vaex as vx
import pyarrow as pa  # noqa
import numpy as np

from ..util import generate_unique_key

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
    # TODO: verify auth status when attempting to load a working group dataset
    datapath = _datapath()

    # fail case for no envvar
    if datapath is None:
        return None

    # fail case for no file found
    try:
        dataset = vx.open(f"{datapath}/{filename}")
        return dataset
    except Exception as e:  # noqa
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
        return pd.DataFrame(data)
    except Exception:
        return None


class State:
    """Holds app-wide state variables"""

    mapping = sl.reactive(open_file('mappings.parquet'))
    datamodel = load_datamodel()
    # initializing app with a simple default to demonstrate functionality
    subset_names = sl.reactive(["A"])
    token = sl.reactive(None)

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        # start with standard open operation
        df = open_file(f'{dataset}.parquet')

        if df is None:
            return

        # force cast flags as a numpy array via my method bypassing pyarrow
        flags = np.array(list(
            df["sdss5_target_flags"].values.to_numpy())).astype("uint8")
        df["sdss5_target_flags"] = flags

        # shuffle to ensure skyplot looks nice, constant seed for reproducibility
        df = df.shuffle(random_state=42)

        # force materialization of column to maximize the performance
        # NOTE: embedded in a worker process, we will eat up significant memory with this command
        #  this is because all workers will materialize the column
        # TODO: to minimize this, we need to add --preload option to solara or FastAPI runner, so that it forks the workers from the base instance.
        # NOTE: vaex has an add_column method, but as stated above, it will overload our worker processes.
        #  for more info, see: https://vaex.io/docs/guides/performance.html
        df = df.materialize()

        return df

    df = sl.reactive(load_dataset("ipl3_partial"))

    columns = sl.reactive(
        df.value.get_column_names() if df.value is not None else None)

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
