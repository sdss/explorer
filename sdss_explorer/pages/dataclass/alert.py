"""Alert system and components"""

import solara as sl
import reacton.ipyvuetify as rv

__all__ = ["Alert", "AlertSystem"]


class Alert:
    """Alert message settings"""

    open = sl.reactive(False)
    message = sl.reactive("")
    color = sl.reactive("")
    closeable = sl.reactive(True)

    @staticmethod
    def update(message, color="info", closeable=True):
        # possible colors are success, info, warning, and error
        Alert.color.set(color)
        Alert.message.set(message)
        Alert.closeable.set(closeable)
        Alert.open.set(True)


@sl.component()
def AlertSystem():
    """Global alert system"""
    with rv.Snackbar(
            class_="d-flex justify-left ma-0 pa-0 rounded-pill",
            v_model=Alert.open.value,
            on_v_model=Alert.open.set,
            color=Alert.color.value,
            multi_line=True,
            top=True,
            timeout=3000.0,
    ) as main:
        rv.Alert(
            class_="d-flex justify-center ma-2",
            value=True,
            type=Alert.color.value,
            # prominent=True,
            dense=True,
            children=[Alert.message.value],
        )
        if Alert.closeable.value:
            sl.Button(
                icon=True,
                icon_name="mdi-close",
                on_click=lambda: Alert.open.set(False),
                text=True,
            )
    return main
