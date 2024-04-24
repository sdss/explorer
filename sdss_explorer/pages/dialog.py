"""New, more flexible function of dialog class, to be added into solara at some point"""

import solara as sl
from typing import Union, List, Callable
from solara.alias import rv as v


@sl.component
def Dialog(
    open: Union[sl.Reactive[bool], bool],
    *,
    on_close: Union[None, Callable[[], None]] = None,
    content: Union[str, sl.Element] = "",
    title: str = "Confirm action",
    ok: Union[str, sl.Element] = "OK",
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
                else:
                    user_on_click_ok = ok.kwargs.get("on_click")
                    ok.kwargs = {**ok.kwargs, "on_click": perform_ok}
                    sl.display(ok)
