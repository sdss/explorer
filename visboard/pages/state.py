from typing import cast
import os

import solara as sl
import vaex as vx


def load_path():
    path = os.getenv(
        "EXPLORER_PATH"
    )  # NOTE: does not expect a slash at end of the var, can account for it in future
    if path:
        return path
    else:
        raise ValueError(
            "Path not defined. Please run: export EXPLORER_PATH=path_to_files")


class State:
    df = sl.reactive(cast(vx.DataFrame, None))
    dataset = sl.reactive("")

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        explorer_path = load_path()
        if dataset is None:
            df = vx.open(f"{explorer_path}/{State.dataset.value}.parquet")
        else:
            df = vx.open(f"{explorer_path}/{dataset}.parquet")
        df = df.shuffle()
        State.df.value = df

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
        datasets = ["apogeenet", "aspcap", "thecannon"]
