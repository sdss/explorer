from typing import Optional, cast

import solara as sl
import vaex as vx


class State:
    view = sl.reactive("histogram")
    df = sl.reactive(cast(Optional[vx.DataFrame], None))
    dataset = sl.reactive("")
    theme = sl.reactive(False)
    style = sl.reactive(cast(str, None))

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        if dataset is None:
            df = vx.open(
                f"/home/riley/rproj/data/{State.dataset.value}.parquet")
        else:
            df = vx.open(f"/home/riley/rproj/data/{dataset}.parquet")
        df = df.shuffle()
        State.df.value = df

    @staticmethod
    def change_theme():
        State.theme.value = not State.theme.value
        if State.theme.value:
            State.style.value = "grey-darken-4"
        else:
            State.style.value = None

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]
        datasets = ["apogeenet", "aspcap", "thecannon"]
