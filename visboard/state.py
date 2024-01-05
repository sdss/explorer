from typing import Optional, cast

import solara as sl
import vaex as vx
import reacton.ipyvuetify as rv

try:
    df_sample = vx.open("/home/riley/uni/rproj/data/astra-clean.parquet")
except:  # noqa
    df_sample = None


class State:
    view = sl.reactive("histogram")
    df = sl.reactive(cast(Optional[vx.DataFrame], None))
    theme = sl.reactive(False)
    style = sl.reactive(cast(str, None))

    @staticmethod
    def load_sample():
        State.df.value = df_sample

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        PlotState.x.value = df.columns[0]
        PlotState.y.value = df.columns[1]
        PlotState.color.value = df.columns[2]
        PlotState.nbins.value = 50
        State.df.value = df

    @staticmethod
    def reset():
        State.df.value = None

    @staticmethod
    def change_theme():
        State.theme.value = not State.theme.value
        if State.theme.value:
            State.style.value = "grey-darken-4"
        else:
            State.style.value = None

    class Lookup:
        views = ["histogram", "histogram2d", "scatter", "skyplot"]


class PlotState:
    # x,y,z/color
    x = sl.reactive("teff")
    y = sl.reactive("logg")
    color = sl.reactive("fe_h")

    # plot parameters/settings
    colorscale = sl.reactive("viridis")
    logx = sl.reactive(False)
    logy = sl.reactive(False)
    flipx = sl.reactive(False)
    flipy = sl.reactive(False)

    # statistics
    nbins = sl.reactive(10)
    bintype = sl.reactive("mean")
    binscale = sl.reactive(None)
    norm = sl.reactive(None)

    # aitoff geo settings
    geo_coords = sl.reactive("ra/dec")

    # all lookup data for types
    Lookup = dict(
        norms=[
            None, "percent", "probability", "density", "probability density"
        ],
        bintypes=["count", "mean", "median", "min", "max"],
        colorscales=[
            "inferno",
            "viridis",
            "jet",
            "solar",
            "plotly3",
            "sunset",
            "sunsetdark",
            "tropic",
            "delta",
            "twilight",
        ],
        binscales=[None, "log1p", "log10"],
    )

    # 3d settings
    logz = sl.reactive(False)
    flipz = sl.reactive(False)
