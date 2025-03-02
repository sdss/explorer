"""PlotState class, used for plot settings."""

import solara as sl
from bokeh.palettes import __palettes__ as colormaps
import colorcet as cc

from .subsets import SubsetState
from .alert import Alert
from .vcdata import VCData

palettes = {k.replace("256", "").lower(): k for k in colormaps if "256" in k}
"""dict: all valid colorscales/palettes for plotting with. Created from colorcet's named palettes and Bokeh's continuous 256 color palettes"""

palettes.update(cc.palette_n.copy())


class PlotState:
    """
    Combination of reactive states which instantiate a specific plot's settings/properties.

    Initializes based on keyword arguments, which are passed via plot creation methods in the ViewCard/GridLayout.

    Attributes:
        plottype (str): the plottype; non-reactive and unchanging
        subset (str): subset key
        columns (list(str)): a list of columns selected. Used in Table views.

        x (str): x column
        y (str): y column

        color (str): color data column
        colorscale (str): colormap
        nbins (int): number of bins for aggregations
        bintype (str): type of aggregation to perform
        logcolor (bool): whether the color data is log-scaled

        logx (bool): whether the x data is log-scaled
        logy (bool): whether the y data is log-scaled
        flipx (bool): whether the x dimension is flipped
        flipy (bool): whether the y dimension is flipped

        xmapping (dict): categorical datamapping for x data
        ymapping (dict): categorical datamapping for y data
        colormapping (dict): categorical datamapping for color data

        Lookup (dict): data for quick lookup
    """

    def __init__(self, plottype, current_key, **kwargs):
        # subset and type states
        self.plottype = str(plottype)
        self.subset = sl.use_reactive(current_key)

        # want target data or stats?
        init_cols = (["sdss_id", "gaia_dr3_source_id"] if
                     (plottype == "targets") else ["g_mag", "snr"])
        self.columns = sl.use_reactive(init_cols)

        # setup init columns, also used for resets;
        # these are STABLE columns, so they should have minimal invalids; even if the dataset is small
        initx = "ra"
        inity = "dec"
        initc = "plx"

        self.x = sl.use_reactive(kwargs.get("x", initx))
        self.y = sl.use_reactive(kwargs.get("y", inity))
        self.color = sl.use_reactive(kwargs.get("color", initc))

        # categorical data mappings
        self.xmapping = dict()  # non-reactive
        self.ymapping = dict()  # non-reactive

        # color props
        self.colormapping = dict()  # non-reactive
        self.colorscale = sl.use_reactive(kwargs.get("colorscale", "inferno"))
        self.logcolor = sl.use_reactive(kwargs.get("logcolor", False))

        # binning props
        init_nbins = 100 if (plottype == "heatmap") else 20
        self.nbins = sl.use_reactive(kwargs.get("nbins", init_nbins))
        self.bintype = sl.use_reactive(kwargs.get("bintype", "mean"))

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
            ],
            colorscales=palettes,
        )

    def swap_axes(self):
        """Swaps current x and y axes."""
        # saves current to p and q
        p = self.x.value
        q = self.y.value
        self.x.value = q
        self.y.value = p

    def reset_values(self):
        """Conditional reset based on if given column/subset is still in list. Triggered by threads in plot_settings."""
        # subset resets
        if self.subset.value not in SubsetState.subsets.value.keys():
            new_subset_key = list(SubsetState.subsets.value.keys())[-1]
            Alert.update(
                f"Subset in view was removed, reset to {SubsetState.subsets.value[new_subset_key].name}",
                color="info",
            )
            self.subset.value = new_subset_key
        try:
            if self.subset_b.value not in SubsetState.subsets.value.keys():
                new_subset_key = list(SubsetState.subsets.value.keys())[-2]
                self.subset_b.value = new_subset_key
        except:
            pass

        valid_columns = SubsetState.subsets.value.get(
            self.subset.value).columns + list(VCData.columns.value.keys())

        # columnar resets for table
        if (self.plottype == "stats") or (self.plottype == "targets"):
            for col in self.columns.value:
                removed_cols = set()
                if col not in valid_columns:
                    removed_cols.add(col)
                # NOTE: i choose to remove quietly on stats table -- its very obvious when it disappears
                # NOTE: you have to do it at the end, because a task can only send 1 state update for rerenders
                self.columns.set(
                    [q for q in self.columns.value if q not in removed_cols])
                return

        # columnar resets for plots
        else:
            if self.x.value not in valid_columns:
                Alert.update("Columns of subset changed! Column reset to 'ra'",
                             color="info")
                self.x.value = "dec"
            if self.plottype != "histogram":
                if self.y.value not in valid_columns:
                    Alert.update(
                        "Columns of subset changed! Column reset to 'dec'",
                        color="info")
                    self.y.value = "dec"
                if self.color.value not in valid_columns:
                    Alert.update(
                        "Columns of subset changed! Column reset to 'ra'",
                        color="info",
                    )
                    self.color.value = "ra"

    def update_subset(self, name: str, b: bool = False):
        """Callback to update subset by name."""
        if not b:
            subset = self.subset
        else:
            subset = self.subset_b
        for k, ss in SubsetState.subsets.value.items():
            if ss.name == name:
                subset.set(k)
                break
        return
