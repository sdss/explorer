from typing import cast
import os

import solara as sl
import reacton.ipyvuetify as rv
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

    mapping = sl.reactive(vx.open(f"{load_datapath()}/mappings.parquet"))
    token = sl.reactive(None)

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.df.value = df

    @staticmethod
    def load_dataset(dataset):
        # get dataset name
        datapath = load_datapath()
        # TODO: verify auth status when attempting to load a working group dataset

        df = vx.open(f"{datapath}/{dataset}.parquet")

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

    columns = sl.reactive(df.value.get_column_names())

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]


class VCData:
    """Virtual column data class"""

    columns = sl.reactive(list())

    @staticmethod
    def add_column(name, expression):
        VCData.columns.value.append((name, expression))

    @staticmethod
    def delete_column(name, expression):
        for n, (colname, _expr) in enumerate(VCData.columns.value):
            if colname == name:
                q = n
                break
        State.df.value.delete_virtual_column(name)
        VCData.columns.value = VCData.columns.value[:q] + VCData.columns.value[
            q + 1:]


class Alert:
    """Alert message settings"""

    open = sl.reactive(False)
    message = sl.reactive("")
    color = sl.reactive("")
    closeable = sl.reactive(True)

    @staticmethod
    def update(message, color="info", closeable=True):
        # possible colors are success, info, warning, and error
        Alert.color.set(color)
        Alert.message.set(message)
        Alert.closeable.set(closeable)
        Alert.open.set(True)


def AlertSystem():
    """Global alert system"""
    with rv.Snackbar(
            class_="d-flex justify-left ma-0 pa-0 rounded-pill",
            v_model=Alert.open.value,
            on_v_model=Alert.open.set,
            color=Alert.color.value,
            multi_line=True,
            top=True,
            timeout=3000.0,
    ) as main:
        rv.Alert(
            class_="d-flex justify-center ma-2",
            value=True,
            type=Alert.color.value,
            # prominent=True,
            dense=True,
            children=[Alert.message.value],
        )
        if Alert.closeable.value:
            sl.Button(
                icon=True,
                icon_name="mdi-close",
                on_click=lambda: Alert.open.set(False),
                text=True,
            )
    return main
