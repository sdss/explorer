"""Subset cards and SubsetState class"""

from typing import Callable
import json
import logging
import time as t
import os
import requests

import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement
from solara.lab import ConfirmationDialog

from ...dataclass import Alert, SubsetState
from ....util import settings
from ..dialog import Dialog
from .subset_filters import ExprEditor, TargetingFiltersPanel

logger = logging.getLogger("dashboard")

# context for updater and renamer
updater_context = sl.create_context(print)  #  dummy func


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
            set_newname("")

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
    router = sl.use_router()
    subset = SubsetState.subsets.value[key]
    default = {"status": "not_run"}
    response, set_response = sl.use_state(default)

    def reset_status():
        """On change and not pending a result, reset"""
        if response["status"] != "in_progress":
            set_response(default)

    sl.use_effect(reset_status, dependencies=[subset])

    def query_task():
        """Runs a GET query continously for the given job of the subset"""
        # TODO: there is probably a much smarter way to do this, this is the easiest though
        local_response = query_job_status()
        while local_response["status"] == "in_progress":
            local_response = query_job_status()
            logger.debug("received response", local_response)
            if local_response["status"] == "complete":
                Alert.update(
                    message=
                    f"Your file for Subset {subset.name} is ready! Hit the download button",
                    color="success",
                )

                # apply to everything and get out
                set_response(local_response)
                break
            elif local_response["status"] == "failed":
                Alert.update(
                    message="File render failed! Please try again, "
                    "and inform system adminstrator if it keeps failing.",
                    color="error",
                )
                set_response(local_response)
                break
            t.sleep(2)
        return

    sl.lab.use_task(query_task, dependencies=[response])

    def query_job_status() -> dict[str, str]:
        """Regular 5s ping to check job state"""
        if response["status"] == "in_progress":
            try:
                resp = requests.get(
                    f"{settings.api_url}/status/{response.get('uid', 0)}")
                try:
                    data = json.loads(resp.text)
                    if data["status"] == "complete":
                        return data
                except Exception:
                    return response
            except Exception as e:
                logger.debug(f"failed to connect: {e}")
                Alert.update("Failed to connect to download sever",
                             color="error")
        return response

    def send_job():
        """Exports subset data to JSON and sends to FastAPI DL sever."""
        from ...dataclass import State
        from dataclasses import asdict

        # serialize & remove columns/df from req
        data = asdict(subset)
        data.pop("columns")
        data.pop("df")
        dataset = data["dataset"]
        try:
            resp = requests.post(
                f"{settings.api_url}/filter_subset/ipl3/{State.datatype}/{dataset}",
                params=data,
                data=json.dumps(data),
            )
            if resp.status_code == 202:
                print("post", json.loads(resp.text))
                Alert.update("Creating file for download! Please wait.")
                set_response(json.loads(resp.text))
        except Exception as e:
            logger.debug(f"failed to connect: {e}")
            Alert.update("Failed to connect to download sever", color="error")
        return

    def click_handler():
        """Handles click events"""
        if (response.get("status") == "not_run") or (response.get("status")
                                                     == "failed"):
            send_job()
        elif response.get("status") == "in_progress":
            query_job_status()
        elif response.get("status") == "complete":
            router.push(
                f"{settings.download_url}/{response.get('filepath', 'foobar')}"
            )

    # color logic
    if response["status"] == "complete":
        color = "green"
    elif response["status"] == "complete":
        color = "red"
    else:
        color = "white"

    with sl.Tooltip("Download subset as csv") as main:
        sl.Button(
            label="",
            icon_name="mdi-download",
            color=color,
            outlined=True if response["status"] == "not_run" else False,
            icon=True,
            text=True,
            on_click=click_handler,
        )

    return main
