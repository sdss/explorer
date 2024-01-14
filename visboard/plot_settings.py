import solara as sl
from typing import cast

from solara.components.columns import Columns
from solara.components.card import Card
from state import State


@sl.component
def show_settings(type, state):
    # plot controls
    if type == "scatter":
        return scatter_menu(state)
    elif type == "histogram":
        return statistics_menu(state)
    elif type == "histogram2d":
        return aggregate_menu(state)
    elif type == "skyplot":
        return sky_menu(state)


@sl.component()
def sky_menu(plotstate):
    df = State.df.value
    columns = list(map(str, df.columns))
    with sl.Columns([1, 1]):
        with Card(margin=0):
            with sl.Column():
                sl.ToggleButtonsSingle(value=plotstate.geo_coords,
                                       values=["ra/dec", "galactic lon/lat"])
            with sl.Row():
                sl.Select(
                    label="Color",
                    values=columns,
                    value=plotstate.color,
                )
                sl.Select(
                    label="Colorscale",
                    values=plotstate.Lookup["colorscales"],
                    value=plotstate.colorscale,
                )
        with Card(margin=0):
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)


@sl.component()
def scatter_menu(plotstate):
    df = State.df.value
    columns = list(map(str, df.columns))
    with sl.Columns([1, 1]):
        with Card(margin=0):
            with Columns([1, 1]):
                sl.Select(
                    "Column x",
                    values=columns,
                    value=plotstate.x,
                )
                sl.Select(
                    "Column y",
                    values=columns,
                    value=plotstate.y,
                )
            sl.Select(
                label="Color",
                values=columns,
                value=plotstate.color,
            )
            sl.Select(
                label="Colorscale",
                values=plotstate.Lookup["colorscales"],
                value=plotstate.colorscale,
            )
        with Card(margin=0):
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                    sl.Switch(label="Log x", value=plotstate.logx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                    sl.Switch(label="Log y", value=plotstate.logy)
            sl.Markdown("### Reactive plotting")
            sl.ToggleButtonsSingle(
                values=["on", "off"],
                value=plotstate.reactive,
            )


@sl.component()
def statistics_menu(plotstate):
    df = State.df.value
    columns = list(map(str, df.columns))
    with sl.Columns([1, 1]):
        with Card(margin=0):
            with sl.Column():
                sl.Select(
                    "Column x",
                    values=columns,
                    value=plotstate.x,
                )
        with Card(margin=0):
            sl.SliderInt(
                label="Number of Bins",
                value=plotstate.nbins,
                step=10,
                min=10,
                max=1e3,
            )
            sl.Select(
                label="Normalization",
                values=plotstate.Lookup["norms"],
                value=plotstate.norm,
            )
    with Card(margin=0):
        with sl.Columns([1, 1, 1], style={"align-items": "center"}):
            sl.Switch(label="Log x", value=plotstate.logx)
            sl.Switch(label="Flip x", value=plotstate.flipx)
            sl.Switch(label="Log y", value=plotstate.logy)


@sl.component()
def aggregate_menu(plotstate):
    df = State.df.value
    columns = list(map(str, df.columns))
    with sl.Columns([1, 1]):
        with Card(margin=0):
            with Columns([1, 1]):
                with sl.Column():
                    sl.Select(
                        "Column x",
                        values=columns,
                        value=plotstate.x,
                    )
                with sl.Column():
                    sl.Select(
                        "Column y",
                        values=columns,
                        value=plotstate.y,
                    )
            sl.Select(
                label="Colorscale",
                values=plotstate.Lookup["colorscales"],
                value=plotstate.colorscale,
            )
            with Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
        with Card(margin=0):
            sl.SliderInt(
                label="Number of Bins",
                value=plotstate.nbins,
                step=2,
                min=2,
                max=500,
            )
            sl.Select(
                label="Binning type",
                values=plotstate.Lookup["bintypes"],
                value=plotstate.bintype,
            )
            if str(plotstate.bintype.value) != "count":
                sl.Select(
                    label="Column to Bin",
                    values=columns,
                    value=plotstate.color,
                )
            sl.Select(
                label="Binning scale",
                values=plotstate.Lookup["binscales"],
                value=plotstate.binscale,
            )
