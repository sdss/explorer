from typing import cast, Callable
import time as t
import os
import dotenv

import solara as sl
import requests as rq
import reacton.ipyvuetify as rv

from solara.lab import headers, ConfirmationDialog  # noqa
from solara.components.input import use_change
from ipyvue import VueWidget

from .state import State, Alert


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
    # TODO: make proper header check
    try:
        raise KeyError
        # print(headers.value["authentication"])
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
        if "502" in response.json()["detail"]:
            assert False, "upstream server error (api.sdss.org/crown)."

        # check response is okay
        assert response.ok, "invalid username or password."

        # set the token
        print("token received:", response.json()["access_token"])
        State.token.set(response.json()["access_token"])

        # save to header
        # TODO: write to header with solara

        return True, ""
    except AssertionError as e:
        print("request failed:", e)
        return False, e


def logout():
    """Forces token reset & expires token."""
    State.token.set("")
    # TODO: update header and tell valis the token is no longer valid
    return


@sl.component()
def LoginButton():
    """Holds login button and prompter."""
    open, set_open = sl.use_state(False)
    logged = check_auth()

    with rv.AppBarNavIcon() as main:
        sl.Button(
            icon_name="mdi-logout-variant" if logged else "mdi-login-variant",
            icon=True,
            outlined=True,
            on_click=lambda: logout if logged else set_open(True),
        )
        LoginPrompt(open, set_open, login)
    return main


@sl.component()
def LoginPrompt(open, set_open, login):
    """The prompt menu for the login"""
    # TODO: cut down on states
    username = sl.use_reactive("")
    password = sl.use_reactive("")
    visible, set_visible = sl.use_state(False)
    processing = sl.use_reactive(False)
    result = sl.use_reactive(False)

    def close():
        """Resets state vars"""
        set_open(False)
        processing.set(False)
        username.value = ""
        password.value = ""

    def validate():
        # keep menu open, process it
        processing.set(True)
        result.value, e = login(username.value, password.value)
        Alert.update(
            "Login successful!" if result.value else "Login failed: " + str(e),
            "success" if result.value else "error",
            closeable=True,
        )
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
