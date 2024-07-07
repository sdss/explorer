"""Main application state variables"""

import os

import solara as sl
import vaex as vx
import pyarrow as pa  # noqa
import numpy as np

from ..util import generate_unique_key

# disable the vaex built-in logging (clogs on FileNotFounds et al)
# TODO: set to only remove on production mode (no reload context; is this registered as a variable i can access?)
# alternatively can I pass it up to valis?
vx.logging.remove_handler()


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


# initial key for subset A
init_key = generate_unique_key("A")


class State:
    """Holds app-wide state variables"""

    mapping = sl.reactive(open_file('mappings.parquet'))
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
