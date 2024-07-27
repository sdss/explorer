"""Util functions for the app"""

import uuid
from typing import Callable

import solara as sl
import vaex as vx  # noqa
from ipyvue import VueWidget

__all__ = ["check_catagorical", "generate_unique_key", "add_keyup_enter_event"]


def check_catagorical(expression: str) -> bool:
    return (expression.dtype == "string") | (expression.dtype == 'bool')


def generate_unique_key(key: str) -> str:
    """Generates a unique UUID-based key for given string."""

    def make_uuid(*_ignore):
        return str(uuid.uuid4())

    return key + make_uuid()


def add_keyup_enter_event(el: sl.Element, callback: Callable):
    """Function to add keyup enter event to a Solara element."""

    def add_event_handler():

        def on_enter(widget, event, data):
            callback(widget.v_model)

        widget: VueWidget = sl.get_widget(el)
        widget.on_event("keyup.enter", on_enter)

        def cleanup():
            widget.on_event("keyup.enter", on_enter, remove=True)

        return cleanup

    sl.use_effect(add_event_handler, dependencies=[])
