import vaex as vx
import solara as sl
from solara.lab import ContextMenu
import plotly.graph_objects as go
import numpy as np

df_loaded = vx.open("/home/riley/uni/rproj/data/astra-clean.parquet")
df_loaded = df_loaded.shuffle()


def range_loop(start, offset):
    return (start + (offset % 360) + 360) % 360


def update_relayout(fig, relayout):
    if relayout is not None:
        if len(relayout) == 0:
            return fig
        if "xaxis.range[0]" in relayout.keys():
            range = [relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]]
            if plotstate.flipx.value:
                range = [np.max(range), np.min(range)]
            else:
                range = [np.min(range), np.max(range)]
            if plotstate.logx.value:
                range = np.log10(range)
            fig.update_xaxes(range=range)
        if "yaxis.range[0]" in relayout.keys():
            range = [relayout["yaxis.range[0]"], relayout["yaxis.range[1]"]]
            if plotstate.flipy.value:
                range = [np.max(range), np.min(range)]
            else:
                range = [np.min(range), np.max(range)]
            if plotstate.logy.value:
                range = np.log10(range)
            fig.update_yaxes(range=range)

        # LONGITUDE
        if "geo.projection.rotation.lon" in relayout.keys():
            fig.update_geos(
                projection_rotation_lon=relayout["geo.projection.rotation.lon"]
            )
        if "geo.center.lon" in relayout.keys():
            fig.update_geos(center_lon=relayout["geo.center.lon"])
        # LATITUDE
        if "geo.projection.rotation.lat" in relayout.keys():
            fig.update_geos(
                projection_rotation_lat=relayout["geo.projection.rotation.lat"]
            )
        if "geo.center.lat" in relayout.keys():
            fig.update_geos(center_lat=relayout["geo.center.lat"])
        if "geo.projection.scale" in relayout.keys():
            fig.update_geos(projection_scale=relayout["geo.projection.scale"])
    return fig


@sl.component()
def Page():
    df = df_loaded
    hovered, set_hovered = sl.use_state(False)
    clicked, set_clicked = sl.use_state(False)
    rerange, set_rerange = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)

    if "geo.projection.scale" in rerange.keys():
        scale = np.max((rerange["geo.projection.scale"], 1.0))
    else:
        scale = 1.0
    if "geo.center.lon" in rerange.keys():
        lon_center = rerange["geo.center.lon"]
    else:
        lon_center = 0
    if "geo.center.lat" in rerange.keys():
        lat_center = rerange["geo.center.lat"]
    else:
        lat_center = 0

    # make filter data
    lonlow, lonhigh = (
        range_loop(0, -180 / scale + lon_center),
        range_loop(0, 180 / scale + lon_center),
    )
    latlow, lathigh = (
        np.max((lat_center - (90 / scale), -90)),
        np.min((lat_center + (90 / scale), 90)),
    )

    # create and set filter objects
    lonfilter = None
    if scale > 1:
        if lonhigh < lonlow:
            lonfilter = df[f"(ra > {lonlow})"] | df[f"(ra < {lonhigh})"]
        else:
            lonfilter = df[f"(ra > {lonlow})"] & df[f"(ra < {lonhigh})"]
    if lonfilter is not None:
        set_local_filter((df[f"(dec > {latlow})"] & df[f"(dec< {lathigh})"])
                         & lonfilter)
    else:
        set_local_filter(df[f"(dec > {latlow})"] & df[f"(dec< {lathigh})"])

    if local_filter is not None:
        dff = df[local_filter]
    else:
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
    x = list(range(0, 360 + dtick, dtick))
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
    fig.update_layout(
        showlegend=False,
        margin={
            "t": 30,
            "b": 10,
            "l": 0,
            "r": 0
        },
        height=900,
        width=1600,
    )
    fig = update_relayout(fig, rerange)
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
                set_rerange({})
                set_local_filter(None)
            else:
                print(type(rerange))
                set_rerange(dict(rerange, **data["relayout_data"]))

    fig = sl.FigurePlotly(
        fig,
        on_relayout=on_relayout,
        on_click=on_click,
        on_hover=on_hover,
        on_unhover=on_unhover,
        dependencies=[
            rerange,
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
