from typing import cast, Callable
import time as t
import os
import dotenv

import solara as sl
import requests as rq
import reacton.ipyvuetify as rv
from solara.lab import task, ConfirmationDialog

from solara.lab import headers
from solara.components.input import use_change
from ipyvue import VueWidget

from .state import State, Alert
from .dialog import Dialog


def get_url():
    """get the valis api url"""
    url = os.getenv("VALIS_API_URL")
    if url is not None:
        return url

    env = os.getenv("VALIS_ENV") or os.getenv("SOLARA_ENV") or ""
    name = (".env.dev" if env.startswith("dev") else
            ".env.test" if env.startswith("test") else ".env.prod")
    dotenv.load_dotenv(dotenv.find_dotenv(name))
    return os.getenv("VALIS_API_URL")


api_url: str = get_url()


def check_auth():
    """Checks if logged in."""
    try:
        # TODO: add verify
        token = headers.value["authorization"]

    except KeyError:
        return False
    return True


def login(username: str, password: str):
    """Request token from username and password."""
    # NOTE: we don't make this asynchronous as we want to lock UI during login
    print("Username:", username)
    print("Password:", password)

    try:
        # check for a username and password
        assert username, "username not specified."
        assert password, "password not specified."

        # check for a response
        response = rq.post(
            api_url + "/auth/login",
            data={
                "username": username,
                "password": password
            },
            # TODO: update JSON to locate variable
            json={
                "release": "dr17",
            },
        )
        print("response received:", response.json())
        if not response.ok:
            assert (
                "502" not in response.json()["detail"]
            ), "upstream server error, please inform admins (api.sdss.org/crown)."

        # check response is okay
        assert response.ok, "invalid username or password."

        # set the token
        print("token received:", response.json()["access_token"])

        # save to header
        # TODO: write to header with solara
        State.token.value = response.json()["access_token"]

        return True, ""
    except AssertionError as e:
        print("request failed:", e)
        return False, e

    return


@sl.component()
def LoginButton():
    """Holds login button and prompter."""
    open, set_open = sl.use_state(False)
    logged, set_logged = sl.use_state(check_auth())
    confirm = sl.use_reactive(False)

    def logout():
        """Forces token reset & expires token."""
        headers.value["credentials"] = ""
        set_logged(False)
        # TODO: update header and tell valis the token is no longer valid

    with rv.AppBarNavIcon() as main:
        sl.Button(
            icon_name="mdi-logout-variant" if logged else "mdi-login-variant",
            icon=True,
            outlined=True,
            on_click=lambda: confirm.set(True) if logged else set_open(True),
        )
        LoginPrompt(open, set_open, set_logged)
        ConfirmationDialog(
            confirm,
            title="Are you sure you want to logout?",
            cancel="no",
            ok="yes",
            on_ok=logout,
        )
    return main


@sl.component()
def LoginPrompt(open, set_open, set_logged):
    """The prompt menu for the login"""
    username = sl.use_reactive("")
    password = sl.use_reactive("")
    error, set_error = sl.use_state(cast(str, None))
    # TODO: ensure this not available as plaintext in debug logs -- big security risk.
    visible, set_visible = sl.use_state(False)

    def close():
        """Resets state vars"""
        set_open(False)
        username.value = ""
        password.value = ""
        set_visible(False)

    @task
    def validate():
        # keep menu open, process it
        if username.value == "" and password.value == "":
            return None
        result, e = login(username.value, password.value)
        if result:
            Alert.update(
                f"Logged in as {username.value}, welcome!",
                color="success",
                closeable=True,
            )
            close()
            set_logged(True)
            return True
        else:
            set_error(e)
            Alert.update(
                f"Login failed: {e}",
                color="error",
            )
            return False

    with Dialog(
            open,
            content="Login to SDSS",
            on_cancel=close,
            ok="Login",
            close_on_ok=False,
            on_ok=validate,
    ):
        uname_field = sl.InputText("Username", value=username)
        pword_field = rv.TextField(
            v_model=password.value,
            append_icon="mdi-eye" if not visible else "mdi-eye-off",
            type="password" if not visible else "text",
            label="Password",
        )
        # NOTE: these reactive updates don't work for some reason
        # if validate.pending:
        #    sl.ProgressLinear(indeterminate=True)
        # elif validate.finished:
        #    if not validate.value:
        #        sl.Error(
        #            label=f"Login failed: {error}",
        #            icon=True,
        #            dense=True,
        #            outlined=False,
        #        )

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
