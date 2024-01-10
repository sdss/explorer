import solara as sl
import vaex as vx
import reacton.ipyvuetify as rv
from solara.components.dataframe import ScatterCard


@sl.component
def Page():
    with rv.Card(style_=" width: 100%; height: 100%"):
        with rv.CardTitle(children=["Plot"]):
            pass
        with rv.CardText():
            with rv.Btn(
                    v_on="x.on",
                    icon=True,
                    absolute=True,
                    style_="right: 10px; top: 10px",
            ) as btn:
                rv.Icon(children=["mdi-settings"])
            with rv.Menu(activator=btn):
                with rv.Card(style_=" width: 100%; height: 100%"):
                    with rv.Btn(icon=True):
                        rv.Icon(children=["mdi-settings"])
                        rv.Html(children=["hi"])


if __name__ == "__main__":
    Page()
