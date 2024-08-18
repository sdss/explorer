"""Subset cards and SubsetState class"""

from typing import Callable

import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement
from solara.lab import ConfirmationDialog

from ...dataclass import Alert, SubsetState
from ..dialog import Dialog
from .subset_filters import ExprEditor, TargetingFiltersPanel

# context for updater and renamer
updater_context = sl.create_context(print)  # context for forcing updates


@sl.component()
def SubsetOptions(key: str, deleter: Callable):
    """
    Contains all subset configuration threads and state variables,
    including expression, cartonmapper, clone and delete.

    Grouped to single namespace to add clone functionality.

    Inputs:
        :key: key for subset
        :deleter: deletion functions
    """
    # filter settings/subfilters
    invert = sl.use_reactive(False)

    # flag data

    # User facing
    with sl.Column() as main:
        ExprEditor(key, invert)
        # complex option panels
        TargetingFiltersPanel(key, invert)
        # bottom card actions
        with rv.Row(style_="width: 100%; height: 100%"):
            # download button
            DownloadMenu(key)

            # invert button
            InvertButton(invert)

            # spacer
            rv.Spacer()

            # rename button
            RenameSubsetButton(key)

            # clone button
            CloneSubsetButton(key)

            # delete button
            DeleteSubsetDialog(deleter)

    return main


@sl.component()
def InvertButton(invert) -> ValueElement:
    with sl.Tooltip("Invert the filters of this subset") as main:
        sl.Button(
            label="",
            icon_name="mdi-invert-colors-off"
            if invert.value else "mdi-invert-colors",
            color="red" if invert.value else None,
            icon=True,
            text=True,
            on_click=lambda: invert.set(not invert.value),
        )
    return main


@sl.component()
def RenameSubsetButton(key: str) -> ValueElement:
    newname, set_newname = sl.use_state("")  # rename dialog state
    rename = sl.use_reactive(False)

    def rename_handler():
        if SubsetState.rename_subset(key, newname=newname):
            rename.set(False)
            set_newname('')

    with sl.Tooltip("Rename this subset"):
        sl.Button(
            label="",
            icon_name="mdi-rename-box",
            icon=True,
            text=True,
            on_click=lambda: rename.set(True),
        )
        with Dialog(
                rename,
                title="Enter a new name for this subset",
                close_on_ok=False,
                on_ok=rename_handler,
                on_cancel=lambda: set_newname(""),
        ):
            sl.InputText(
                label="Subset name",
                value=newname,
                on_value=set_newname,
            )


@sl.component()
def CloneSubsetButton(key: str) -> ValueElement:
    with sl.Tooltip("Clone this subset") as main:
        sl.Button(
            label="",
            icon_name="mdi-content-duplicate",
            icon=True,
            text=True,
            on_click=lambda: SubsetState.clone_subset(key),
        )
    return main


@sl.component()
def DeleteSubsetDialog(deleter: Callable) -> ValueElement:
    # confirmation dialog for deletion
    delete = sl.use_reactive(False)
    with sl.Tooltip("Delete this subset") as main:
        sl.Button(
            label="",
            icon_name="mdi-delete-outline",
            icon=True,
            text=True,
            disabled=True if len(SubsetState.subsets.value) <= 1 else False,
            color="red",
            on_click=lambda: delete.set(True),
        )
        ConfirmationDialog(
            delete,
            title="Are you sure you want to delete this subset?",
            ok="yes",
            cancel="no",
            on_ok=deleter,
        )
    return main


@sl.component()
def DownloadMenu(key: str) -> ValueElement:

    def get_data():
        # TODO: change all of these methods to better valis-integrated methods that dont involve
        # dropping the entire DB file into memory...
        # dfp = dff.to_pandas_df()
        Alert.update(
            "Download currently unsupported due to memory issues server-side. Coming soon!",
            color="info",
        )
        return  # dfp.to_csv(index=False)

    with sl.Tooltip("Download subset as csv") as main:
        sl.Button(
            label="",
            icon_name="mdi-download",
            icon=True,
            text=True,
            on_click=get_data,
            # NOTE: temporary disable because the interface is poor
        )

    return main
