import solara as sl
import vaex as vx
from bokeh.palettes import __palettes__ as colormaps

df = vx.open(
    "/home/riley/projects/explorer/data/ipl3/explorerAllStar-0.6.0.hdf5"
)  # vx.example()[:30_000]
df = df[df["pipeline"] == "best"]
df = df.copy().extract().materialize()
# data = np.array(["foo" if i < len(df) // 2 else "bar" for i in range(len(df))])
# data[:10_000] = "teodddd"
# data2 = np.array(
#    ["lco25m" if i < len(df) // 3 else "apo25m" for i in range(len(df))])
# df["category"] = data
# df["category2"] = data2
# df = df.materialize("category")
# df = df.materialize("category2")


def gen_tooltips(state):
    """Helper function to generate tooltips"""
    tooltips = []
    tooltips.append((state.x.value, "$x"))
    tooltips.append((state.y.value, "$y"))
    if state.plottype.value == "heatmap":
        tooltips.append((state.bintype.value, "@z"))

    return tooltips


class GridState:
    index = sl.reactive(0)
    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    states = sl.reactive([])


class PlotState:
    """
    Combination of reactive states which instantiate a specific plot's settings/properties.

    Initializes based on keyword arguments, which are passed via plot creation methods in the ViewCard/GridLayout.

    Attributes:
        plottype(str): the plottype; non-reactive and unchanging
    """

    def __init__(self, plottype, current_key, **kwargs):
        # subset and type states
        self.plottype = str(plottype)
        self.subset = sl.use_reactive(current_key)

        self.columns = sl.use_reactive(["g_mag", "bp_mag"])
        self.x = sl.use_reactive(kwargs.get("x", "teff"))
        self.y = sl.use_reactive(kwargs.get("y", "logg"))
        self.color = sl.use_reactive(kwargs.get("color", "fe_h"))

        # categorical data mappings
        self.xmapping = dict()  # non-reactive
        self.ymapping = dict()  # non-reactive

        # color props
        self.colormapping = dict()  # non-reactive
        self.colorscale = sl.use_reactive(
            kwargs.get("colorscale", "Inferno256"))
        self.logcolor = sl.use_reactive(kwargs.get("logcolor", False))

        # binning props
        self.nbins = sl.use_reactive(200)
        init_bintype = "mean" if (plottype == "heatmap") else "count"
        self.bintype = sl.use_reactive(kwargs.get("bintype", init_bintype))

        # flips and logs
        self.flipx = sl.use_reactive(bool(kwargs.get("flipx", "")))
        self.flipy = sl.use_reactive(bool(kwargs.get("flipy", "")))
        self.logx = sl.use_reactive(bool(kwargs.get("logx", "")))
        self.logy = sl.use_reactive(bool(kwargs.get("logy", "")))

        # all lookup data for plottypes
        # TODO: move this lookup data elsewhere to reduce the size of the plotstate objects
        self.Lookup = dict(
            bintypes=[
                "count",
                "mean",
                "median",
                "sum",
                "min",
                "max",
                "mode",
                "cov",
                "covar",
            ],
            colorscales=[map for map in colormaps if "256" in map],
            projections=[
                "albers",
                "aitoff",
                "azimuthal equal area",
                "equal earth",
                "hammer",
                "mollweide",
                "mt flat polar quartic",
            ],
        )

    def swap_axes(self):
        # saves current to p and q
        p = self.x.value
        q = self.y.value
        self.x.value = q
        self.y.value = p
