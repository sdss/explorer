from typing import cast
import os

import solara as sl
import vaex as vx
import pyarrow as pa  # noqa
import numpy as np


def load_datapath():
    """fetches path to parquet files from envvar"""
    datapath = os.getenv(
        "EXPLORER_DATAPATH"
    )  # NOTE: does not expect a slash at end of the envvar, can account for it in future
    if datapath:
        return datapath
    else:
        raise ValueError(
            "Path not defined. Please run: export EXPLORER_DATAPATH=path_to_files"
        )


class State:
    """Holds app-wide state"""

    dataset = sl.reactive("")
    df = sl.reactive(cast(vx.DataFrame, None))
    flags = sl.reactive(cast(vx.DataFrame, None))
    token = sl.reactive("")  # access token
    mapping = sl.reactive(vx.open(f"{load_datapath()}/mappings.parquet"))
    datasets = [
        "apogeenet",
        "aspcap",
        "thecannon",
    ]  # TODO: convert to a function which http.get requests to find the list of "releases" for given authorization level

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        # get dataset name
        State.dataset.value = dataset
        datapath = load_datapath()
        # TODO: verify auth status when attempting to load a working group dataset

        # stupid bug fix
        if dataset is None:
            df = vx.open(f"{datapath}/{State.dataset.value}.parquet")
        else:
            df = vx.open(f"{datapath}/{dataset}.parquet")

        # force cast flags as a numpy array via my method bypassing pyarrow
        flags = np.array(list(
            df["sdss5_target_flags"].values.to_numpy())).astype("uint8")
        df["sdss5_target_flags"] = flags

        # shuffle to ensure skyplot looks nice, constant seed for reproducibility
        df = df.shuffle(random_state=42)

        State.df.value = df

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
