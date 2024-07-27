"""New, more flexible function of dialog class, to be added into solara at some point"""
from typing import Any, Callable, Optional, TypeVar, Union, cast, overload, List, Dict

import solara as sl
from solara.alias import rv as v
from solara.components.input import use_change


@sl.component()
def InputTextAF(
    label: str,
    value: Union[str, sl.Reactive[str]] = "",
    on_value: Callable[[str], None] = None,
    disabled: bool = False,
    password: bool = False,
    continuous_update: bool = False,
    update_events: List[str] = ["focusout", "keyup.enter"],
    error: Union[bool, str] = False,
    message: Optional[str] = None,
    autofocus: bool = False,
    classes: List[str] = [],
    style: Optional[Union[str, Dict[str, str]]] = None,
):
    """Free form text input (with exposed autofocus prop).

    * `label`: Label to display next to the slider.
    * `value`: The currently entered value.
    * `on_value`: Callback to call when the value changes.
    * `disabled`: Whether the input is disabled.
    * `password`: Whether the input is a password input (typically shows input text obscured with an asterisk).
    * `continuous_update`: Whether to call the `on_value` callback on every change or only when the input loses focus or the enter key is pressed.
    * `update_events`: A list of events that should trigger `on_value`. If continuous update is enabled, this will effectively be ignored,
        since updates will happen every change.
    * `error`: If truthy, show the input as having an error (in red). If a string is passed, it will be shown as the error message.
    * `message`: Message to show below the input. If `error` is a string, this will be ignored.
    * `autofocus`: Whether to force focus to window on render. Useful for dialog menus.
    * `classes`: List of CSS classes to apply to the input.
    * `style`: CSS style to apply to the input.
    """
    reactive_value = sl.use_reactive(value, on_value)
    del value, on_value
    style_flat = sl.util._flatten_style(style)
    classes_flat = sl.util._combine_classes(classes)

    def set_value_cast(value):
        reactive_value.value = str(value)

    def on_v_model(value):
        if continuous_update:
            set_value_cast(value)

    messages = []
    if error and isinstance(error, str):
        messages.append(error)
    elif message:
        messages.append(message)
    text_field = v.TextField(
        v_model=reactive_value.value,
        on_v_model=on_v_model,
        label=label,
        disabled=disabled,
        type="password" if password else None,
        error=bool(error),
        autofocus=autofocus,
        messages=messages,
        class_=classes_flat,
        style_=style_flat,
    )
    use_change(text_field,
               set_value_cast,
               enabled=not continuous_update,
               update_events=update_events)
    return text_field


@sl.component
def Dialog(
    open: Union[sl.Reactive[bool], bool],
    *,
    on_close: Union[None, Callable[[], None]] = None,
    content: Union[str, sl.Element] = "",
    title: str = "Confirm action",
    ok: Union[Optional[str], sl.Element] = "OK",
    on_ok: Callable[[], None] = lambda: None,
    ok_enable: Union[sl.Reactive[bool], bool] = True,
    close_on_ok: bool = True,
    cancel: Union[str, sl.Element] = "Cancel",
    on_cancel: Callable[[], None] = lambda: None,
    children: List[sl.Element] = [],
    max_width: Union[int, str] = 500,
    persistent: bool = False,
):

    def on_open(open_value):
        if not open_value:
            if on_close:
                on_close()

    open_reactive = sl.use_reactive(open, on_open)
    ok_reactive = sl.use_reactive(ok_enable)
    del open
    del ok_enable

    def close():
        open_reactive.set(False)

    user_on_click_ok = None
    user_on_click_cancel = None

    def perform_ok():
        if user_on_click_ok:
            user_on_click_ok()
        on_ok()
        if close_on_ok:
            close()

    def perform_cancel():
        if user_on_click_cancel:
            user_on_click_cancel()
        on_cancel()
        close()

    def on_v_model(value):
        if not value:
            on_cancel()
        open_reactive.set(value)

    with v.Dialog(
            v_model=open_reactive.value,
            on_v_model=on_v_model,
            persistent=persistent,
            max_width=max_width,
    ):
        with sl.v.Card():
            sl.v.CardTitle(children=[title])
            with sl.v.CardText(style_="min-height: 64px"):
                if isinstance(content, str):
                    sl.Text(content)
                else:
                    sl.display(content)
                if children:
                    sl.display(*children)
            with sl.v.CardActions(class_="justify-end"):
                if isinstance(cancel, str):
                    sl.Button(
                        label=cancel,
                        on_click=perform_cancel,
                        text=True,
                        classes=["grey--text", "text--darken-2"],
                    )
                else:
                    # the user may have passed in on_click already
                    user_on_click_cancel = cancel.kwargs.get("on_click")
                    # override or add our own on_click handler
                    cancel.kwargs = {
                        **cancel.kwargs, "on_click": perform_cancel
                    }
                    sl.display(cancel)

                # similar as cancel
                if isinstance(ok, str):
                    sl.Button(
                        label=ok,
                        on_click=perform_ok,
                        dark=True,
                        color="primary",
                        disabled=not ok_reactive.value,
                        elevation=0,
                    )
                elif ok is None:
                    # no ok button
                    pass
                else:
                    user_on_click_ok = ok.kwargs.get("on_click")
                    ok.kwargs = {**ok.kwargs, "on_click": perform_ok}
                    sl.display(ok)
