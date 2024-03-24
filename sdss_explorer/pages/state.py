from typing import cast, Optional
import os

import solara as sl
import vaex as vx


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
    token = sl.reactive("")  # access token
    mapping = sl.reactive(vx.open(f"{load_datapath()}/bitmappings.csv"))
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
        State.dataset.value = dataset
        datapath = load_datapath()
        # TODO: verify auth status when attempting to load a working group dataset
        if dataset is None:
            df = vx.open(f"{datapath}/{State.dataset.value}.parquet")
        else:
            df = vx.open(f"{datapath}/{dataset}.parquet")
        df = df.shuffle()
        State.df.value = df

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
