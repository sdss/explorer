from typing import cast, Callable
import time as t
import asyncio
import solara as sl
import reacton.ipyvuetify as rv

from solara.lab import headers, ConfirmationDialog, task
from solara.components.input import use_change
from ipyvue import VueWidget


def check_auth():
    """Checks if logged in."""
    # TODO: make proper header check
    try:
        print(headers.value["authentication"])
    except KeyError:
        return False
    return True


def login(username, password):
    """Convert username and password to token."""
    # NOTE: we don't make this asynchronous as we want to lock UI during login
    print("Username:", username)
    print("Password:", password)
    t.sleep(2)  # temp to show progress bar
    # TODO: convert login details to token + update the header (valis)
    return


def logout():
    """Force expire token and logout."""
    print("Logging out...")
    # TODO: update header and use valis
    return


@sl.component()
def LoginButton():
    """Holds login button and prompter"""
    open, set_open = sl.use_state(False)
    logged = check_auth()

    sl.Button(
        icon_name="mdi-logout-variant" if logged else "mdi-login-variant",
        icon=True,
        outlined=True,
        on_click=lambda: logout if logged else set_open(True),
        classes=["purple"],
    )
    LoginPrompt(open, set_open, login)


@sl.component()
def LoginPrompt(open, set_open, login):
    """The prompt menu for the login"""
    username = sl.use_reactive("")
    password = sl.use_reactive("")
    visible, set_visible = sl.use_state(False)
    processing = sl.use_reactive(False)

    def close():
        """Resets state vars"""
        set_open(False)
        processing.set(False)
        username.value = ""
        password.value = ""

    def validate():
        # keep menu open, process it
        set_open(True)
        processing.set(True)
        login(username.value, password.value)
        processing.set(False)
        close()

    with ConfirmationDialog(open,
                            content="Login to SDSS",
                            on_cancel=close,
                            ok="Login",
                            on_ok=validate):
        sl.ProgressLinear(value=processing.value)
        uname_field = sl.InputText("Username", value=username)
        pword_field = rv.TextField(
            v_model=password.value,
            append_icon="mdi-eye" if not visible else "mdi-eye-off",
            type="password" if not visible else "text",
            label="Password",
        )
        use_change(pword_field,
                   password.set,
                   update_events=["blur", "keyup.enter"])
        use_append(
            uname_field,
            pword_field,
            username.set,
            password.set,
            lambda *ignore_args: set_visible(not visible),
        )


def use_append(
    ufield: sl.Element,
    pfield: sl.Element,
    on_uname: Callable,
    on_pword: Callable,
    on_visible: Callable,
):
    """Effects to save variables when visibility toggle is pressed."""
    on_pword_ref = sl.use_ref(on_pword)
    on_pword_ref.current = on_pword
    on_visible_ref = sl.use_ref(on_visible)
    on_visible_ref.current = on_visible
    on_uname_ref = sl.use_ref(on_uname)
    on_uname_ref.current = on_uname

    def add_events():
        uwidget = cast(VueWidget, sl.get_widget(ufield))

        def on_change(widget, event, data):
            on_uname_ref.current(uwidget.v_model)
            on_pword_ref.current(widget.v_model)
            on_visible_ref.current(not on_visible_ref)  # flips visibility

        widget = cast(VueWidget, sl.get_widget(pfield))
        widget.on_event("click:append", on_change)

        def cleanup():
            widget.on_event("click:append", on_change, remove=True)

        return cleanup

    sl.use_effect(add_events, [True])
