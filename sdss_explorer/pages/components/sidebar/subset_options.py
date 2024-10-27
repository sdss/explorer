"""Subset cards and SubsetState class"""

from typing import Callable

import os
import reacton.ipyvuetify as rv
import solara as sl
from timeit import default_timer as timer
from reacton.core import ValueElement
from solara.lab import ConfirmationDialog, task

from ...util import generate_unique_key

from ...dataclass import Alert, SubsetState, State, use_subset
from ..dialog import Dialog
from .subset_filters import ExprEditor, TargetingFiltersPanel

# context for updater and renamer
updater_context = sl.create_context(print)  # context for forcing updates

SCRATCH = os.getenv('EXPLORER_SCRATCH', default=None)


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
    """
    Download Menu for subset
    """
    df = State.df.value
    subset = SubsetState.subsets.value[key]
    filter, _ = use_subset(id(df), key, name='download')
    if filter:
        dff = df[filter]
    else:
        dff = df

    @task(prefer_threaded=True)
    def get_data():
        # export data
        # NOTE: chunk size is 1/8th normal export rate
        try:
            assert SCRATCH is not None, 'EXPLORER_SCRATCH was not set! Please fix.'
            path = os.path.join(SCRATCH, f"{State.uuid}/")
            filename = f'{subset.name}-{generate_unique_key()}.csv'
            os.makedirs(path, exist_ok=True)
            route = os.path.join(path, filename)
            dffx = dff.drop(
                'sdss5_target_flags',
                check=True)  # NOTE: does this drop from everywhere else?
            print(f'saving to {route}')
            start = timer()
            dffx.export_csv(route,
                            progress=True,
                            parallel=True,
                            backend='arrow')

            print('finished!', timer() - start)

            Alert.update(f'Subset {subset.name} is ready for download!',
                         color='success')
            print('returning...')
            return route
        except Exception as e:
            print(f"Error on {State.uuid}", get_data.exception)
            Alert.update(
                f'Subset {subset.name} failed to export for download!',
                color='error')
            assert False

    with sl.Tooltip("Download subset as csv"):
        if (get_data.not_called) or (get_data.error):
            sl.Button(
                label="",
                icon_name="mdi-download",
                icon=True,
                text=True,
                on_click=get_data,
            )
        elif (get_data.finished) and (not get_data.error):
            sl.Button(
                label="",
                icon_name="mdi-download",
                attributes={'href': 'file://' + str(get_data.value)},
                color='green',
                icon=True,
                text=True,
            )

        elif get_data.pending:
            rv.ProgressCircular(indeterminate=True)

    return
