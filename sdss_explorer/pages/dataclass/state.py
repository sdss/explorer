"""Main application state variables"""

import os

import solara as sl
import reacton.ipyvuetify as rv
import vaex as vx
import pyarrow as pa  # noqa
import numpy as np

from ..util import generate_unique_key


def _datapath():
    """fetches path to parquet files from envvar"""
    datapath = os.getenv(
        "EXPLORER_DATAPATH"
    )  # NOTE: does not expect a slash at end of the envvar, can account for it in future
    if datapath:
        return datapath
    else:
        return None


def _load_check(filename):
    """Pre-loader to check for loading errors"""
    # get dataset name
    # TODO: verify auth status when attempting to load a working group dataset
    datapath = _datapath()

    # fail case for no envvar
    if datapath is None:
        return False

    # fail case for no file found
    try:
        vx.open(f"{datapath}/{filename}")
    except FileNotFoundError:
        return False

    return True


# initial key for subset A
init_key = generate_unique_key("A")


class State:
    """Holds app-wide state variables"""

    mapping = sl.reactive(
        vx.open(f"{_datapath()}/mappings.parquet"
                ) if _load_check("mappings.parquet") else None)
    subsets = sl.reactive(
        {init_key: "A"})  # Dict[str,str]; initialization done in SubsetCard
    # initializing app with a simple default to demonstrate functionality
    subset_names = sl.reactive(["A"])
    token = sl.reactive(None)

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        # fail case for no file found/dne OR no envvar
        if not _load_check(f"{dataset}.parquet"):
            return None

        df = vx.open(f"{_datapath()}/{dataset}.parquet")

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

    columns = sl.reactive(df.value.get_column_names(
    ) if load_dataset("ipl3_partial") is not None else None)

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
