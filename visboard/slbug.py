import vaex as vx
import solara as sl
from solara.lab import ContextMenu
import plotly.graph_objects as go
import numpy as np


@sl.component()
def Page():
    df = vx.open("/home/riley/uni/rproj/data/astra-clean.parquet")
    hovered, set_hovered = sl.use_state(False)
    clicked, set_clicked = sl.use_state(False)
    rerange = sl.use_reactive({})

    dff = df
    dff = dff[:3_000]
    dtick = 30  # for tickers

    lon = dff["ra"]
    lat = dff["dec"]
    fig = go.Figure(data=go.Scattergeo(
        lat=lat.values,
        lon=lon.values,
        mode="markers",
    ), )
    x = list(range(-180, 180 + dtick, dtick))
    y = list(range(-90, 90 + dtick, dtick))
    xpos = 0
    ypos = 0
    fig.add_trace(
        go.Scattergeo({
            "lon": x + [xpos] * (len(y)),
            "lat": [ypos] * (len(x)) + y,
            "showlegend": False,
            "text": x + y,
            "mode": "text",
        }))

    fig.update_geos(
        bgcolor="#ccc",
        projection_type="mollweide",
        visible=False,
        lonaxis_showgrid=True,
        lonaxis_tick0=0,
        lataxis_showgrid=True,
        lataxis_tick0=0,
    )
    fig.update_layout(showlegend=False,
                      margin={
                          "t": 30,
                          "b": 10,
                          "l": 0,
                          "r": 0
                      })
    """
    Context Menu handlers
    """

    def on_click(data):
        set_clicked(True)

    def on_hover(data):
        set_clicked(False)
        set_hovered(True)

    def on_unhover(data):
        if not clicked:
            set_hovered(False)

    """
    relayout callback
    """

    def on_relayout(data):
        if data is not None:
            if "geo.fitbounds" in data["relayout_data"].keys():
                print("a")
                rerange.value = {}
            else:
                print("b")
                rerange.value.update(data["relayout_data"])
                print(rerange.value)

            if "geo.projection.scale" in rerange.value.keys():
                scale = rerange.value["geo.projection.scale"]
            else:
                scale = 1.0
            if "geo.center.lon" in rerange.value.keys():
                lon_center = rerange.value["geo.center.lon"]
            else:
                lon_center = 0
            lonrange = [
                lon_center + 180 + (180 / scale),
                lon_center + 180 + (180 / scale),
            ]
            lonrange = [lonrange[0] % 180 - 180, lonrange[1] % 180]
            print(lonrange)

    fig = sl.FigurePlotly(
        fig,
        on_relayout=on_relayout,
        on_click=on_click,
        on_hover=on_hover,
        on_unhover=on_unhover,
        dependencies=[
            filter,
        ],
    )

    with ContextMenu(activator=fig):
        if clicked and hovered:
            text = "clicked and hovered"
        elif clicked and not hovered:
            text = "clicked, not hovered"
        elif hovered and not clicked:
            text = "not clicked, hovered"
        else:
            text = "neither"
        sl.Column(
            gap="0px",
            children=[sl.Card(title=text)],
        )
    return


if __name__ == "__main__":
    Page()
