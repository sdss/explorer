"""Subset options menu component, contains everything under the subset header."""

from typing import Callable
from urllib.parse import urljoin
import json
import logging
import requests
import asyncio

import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement
from solara.lab import ConfirmationDialog

from ...dataclass import Alert, SubsetState
from ....util import settings
from ..dialog import Dialog
from .subset_filters import (
    ExprEditor,
    TargetingFiltersPanel,
    CrossmatchPanel,
    DatasetSelect,
)

logger = logging.getLogger("dashboard")


@sl.component()
def SubsetOptions(key: str, deleter: Callable):
    """
    Contains all subset configuration threads and state variables,
    including expression, cartonmapper, clone and delete.

    Grouped to single namespace to add clone functionality.

    Args:
        key: key for subset
        deleter: deletion functions
    """
    # filter settings/subfilters
    subset = SubsetState.subsets.value[key]
    invert = sl.use_reactive(False)
    open, set_open = sl.use_state([])
    dataset, set_dataset = (
        subset.dataset,
        lambda arg: SubsetState.update_subset(key, dataset=arg),
    )

    # flag data

    # User facing
    with sl.Column() as main:
        if subset.df is not None:
            ExprEditor(key, invert)
            DatasetSelect(key, dataset, set_dataset)
            # complex option panels
            with rv.ExpansionPanels(flat=True,
                                    multiple=True,
                                    v_model=open,
                                    on_v_model=set_open):
                TargetingFiltersPanel(key, invert)
                CrossmatchPanel(key)

            # bottom card actions
            with rv.Row(style_="width: 100%; height: 100%"):
                DownloadMenu(key)  # download button
                InvertButton(invert)  # invert button
                rv.Spacer()  # spacer
                RenameSubsetButton(key)  # rename button
                CloneSubsetButton(key)  # clone button
                DeleteSubsetDialog(deleter)  # delete button

    return main


@sl.component()
def InvertButton(invert) -> ValueElement:
    """Invert subset button

    Args:
        invert (solara.Reactive[bool]): invert setting

    """
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
    """Rename subset button

    Note:
        Calls `SubsetState.rename_subset`

    Args:
        key: subset key

    """
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
    """Clone subset button

    Note:
        Calls `SubsetState.clone_subset`

    Args:
        key: subset key

    """
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
    """Delete subset dialog

    Args:
        deleter: deletion function to remove from SubsetState

    """
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
    """Download menu and button

    Note:
        **THIS CONTAINS ALL FUNCTIONALITY FOR QUERYING `sdss_explorer.server`**

    Args:
        key: subset key
    """

    router = sl.use_router()
    subset = SubsetState.subsets.value[key]
    response, set_response = sl.use_state({"status": "not_run"})

    def reset_status():
        """On change and not pending a result, reset"""
        logger.debug(f"Resetting download button on {subset.name}")
        default = {"status": "not_run"}
        if response["status"] != "in_progress":
            set_response(default)

    sl.use_effect(reset_status, dependencies=[subset])

    def query_job_status(uid: str) -> dict[str, str]:
        """Ping command to query job state and return result

        Args:
            uid: job ID

        Returns:
            data: Dictionary of response data
            response: previous response data (when failing)
        """
        try:
            resp = requests.get(urljoin(settings.api_url, f"status/{uid}"))
            if resp.status_code == 200:
                data = json.loads(resp.text)
                return data
        except Exception as e:
            logger.debug(f"failed to connect: {e}")
            Alert.update("Failed to connect to download sever", color="error")
        return response

    # @sl.lab.task()
    async def query_task():
        """Runs a GET query continously for the given job of the subset"""
        logger.debug(f"query task start on {subset.name}")

        # get our local response
        local_response = response.copy()
        status = local_response.get("status", "in_progress")

        # early exit if something else triggered update (reset, completion, etc)
        if (status == "complete") or (status == "failed") or (status
                                                              == "not_run"):
            return

        # loop until received, spawning in thread
        while True:
            local_response = await asyncio.to_thread(query_job_status,
                                                     local_response["uid"])
            logger.debug(f"received response {local_response}")

            if local_response["status"] == "complete":
                logger.debug(f"job returned as complete! {local_response}")
                Alert.update(
                    message=
                    f"Your file for Subset {subset.name} is ready! Hit the download button",
                    color="success",
                )

                # apply to everything and get out
                set_response(local_response)
                break
            elif local_response["status"] == "failed":
                logger.debug(f"job returned as failed! {local_response}")
                Alert.update(
                    message="File render failed! Please try again, "
                    "and inform system adminstrator if it keeps failing.",
                    color="error",
                )
                set_response(local_response)
                break

            # if not run or in_progress, continues
            await asyncio.sleep(2)

        # flag our exit
        logger.debug(f"query task shutdown on {subset.name}")
        return

    sl.lab.use_task(query_task, dependencies=[response])

    def send_job():
        """Exports subset data to JSON and sends to FastAPI DL sever."""
        from ...dataclass import State
        from dataclasses import asdict

        # serialize & remove columns/df from req
        data = asdict(subset)
        data.pop("columns")
        data.pop("df")
        dataset = data["dataset"]
        jsonData = json.dumps(data)
        logger.debug("requesting" + str(jsonData))
        try:
            # TODO: no idea how requests works
            resp = requests.post(
                urljoin(
                    settings.api_url,
                    f"filter_subset/{State.release}/{State.datatype}/{dataset}",
                ),
                params=data,
                data=jsonData,
            )
            if resp.status_code == 202:
                # ready! push update to call query loop task
                logger.debug("Successfully called for download for" +
                             subset.name)
                Alert.update("Creating file for download! Please wait.")
                set_response(json.loads(resp.text))
        # on timeout raise, inform user
        except Exception as e:
            logger.debug(f"failed to connect to call for download: {e}")
            Alert.update("Failed to connect to download sever", color="error")
        return

    def click_handler():
        """Handles click events"""
        if (response.get("status") == "not_run") or (response.get("status")
                                                     == "failed"):
            send_job()
        elif response.get("status") == "complete":
            logger.debug(
                f"sending user to {settings.download_url}{response.get('filepath', 'foobar')}"
            )

    # color logic
    if response["status"] == "complete":
        color = "green"
    elif response["status"] == "failed":
        color = "red"
    else:
        color = "white"
    button = sl.Button(
        label="",
        icon_name="mdi-download",
        color=color,
        disabled=True if response["status"] == "in_progress" else False,
        icon=True,
        text=True,
        href=
        f"{urljoin(settings.download_url, response.get('filepath', 'foobar'))}"
        if response["status"] == "complete" else None,
        target="_blank",
        on_click=click_handler,
    )

    tooltipped = rv.Tooltip(
        bottom=True,
        disabled=True if response["status"] == "complete" else False,
        v_slots=[{
            "name": "activator",
            "variable": "tooltip",
            "children": [button]
        }],
        color=None,  # pyright: ignore[]
        children=["Download subset"],
    )

    def set_v_on():
        widget = sl.get_widget(button)
        widget.v_on = "tooltip.on"  # pyright: ignore

    sl.use_effect(set_v_on, button)

    return sl.Column(children=[tooltipped])
