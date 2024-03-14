from typing import cast

import solara as sl
import vaex as vx


class State:
    df = sl.reactive(cast(vx.DataFrame, None))
    dataset = sl.reactive("")

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        if dataset is None:
            df = vx.open(f"../../data/{State.dataset.value}.parquet")
        else:
            df = vx.open(f"../../data/{dataset}.parquet")
        df = df.shuffle()
        State.df.value = df

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
        datasets = ["apogeenet", "aspcap", "thecannon"]
