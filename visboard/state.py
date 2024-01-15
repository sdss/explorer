from typing import Optional, cast

import solara as sl
import vaex as vx

try:
    df_sample = vx.open("./astra-clean.parquet")
except:  # noqa
    df_sample = vx.example()


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
    """
    Combination of reactive states which instantiate a specific plot's settings/properties
    """

    def __init__(self):
        # x,y,z/color
        self.x = sl.use_reactive("teff")
        self.y = sl.use_reactive("logg")
        self.color = sl.use_reactive("fe_h")

        # plot parameters/settings
        self.colorscale = sl.use_reactive("viridis")
        self.logx = sl.use_reactive(False)
        self.logy = sl.use_reactive(False)
        self.flipx = sl.use_reactive(False)
        self.flipy = sl.use_reactive(False)
        self.reactive = sl.use_reactive("on")

        # statistics
        self.nbins = sl.use_reactive(10)
        self.bintype = sl.use_reactive("mean")
        self.binscale = sl.use_reactive(None)
        self.norm = sl.use_reactive(None)

        # aitoff geo settings
        self.geo_coords = sl.use_reactive("ra/dec")

        # all lookup data for types
        self.Lookup = dict(
            norms=[
                None, "percent", "probability", "density",
                "probability density"
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


class TableState:
    """
    Adaptive state object for the table view, holding unique properties to that table view.

    """

    def __init__(self, height):
        self.height = sl.use_reactive(height)
