"""Text field with exposed components"""

from typing import Optional, List, Union, Callable, Dict

import solara as sl
import reacton.ipyvuetify as rv

__all__ = ["InputTextExposed"]


@sl.component()
def InputTextExposed(
    label: str,
    value: Union[str, sl.Reactive[str]] = "",
    on_value: Callable[[str], None] = None,
    disabled: bool = False,
    password: bool = False,
    continuous_update: bool = False,
    update_events: List[str] = ["focusout", "keyup.enter"],
    error: Union[bool, str] = False,
    message: Optional[str] = None,
    loading: Optional[bool] = False,
    hint: Optional[str] = None,
    placeholder: Optional[str] = None,
    classes: List[str] = [],
    style: Optional[Union[str, Dict[str, str]]] = None,
    **kwargs,
):
    """Free form text input with hint and messages exposed

    ## Arguments

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
    text_field = rv.TextField(
        v_model=reactive_value.value,
        on_v_model=on_v_model,
        label=label,
        disabled=disabled,
        type="password" if password else None,
        error=bool(error),
        hint=hint,
        persistent_placeholder=False,
        persistent_hint=False,
        placeholder=placeholder,
        loading=loading,
        validate_on_blur=True,
        messages=messages,
        outlined=True,  # zora-like styling
        class_=classes_flat,
        style_=style_flat,
        **kwargs,
    )
    from solara.components.input import use_change

    use_change(
        text_field,
        set_value_cast,
        enabled=not continuous_update,
        update_events=update_events,
    )
    return text_field
