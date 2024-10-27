"""All interactive plot elements, complete with widget effects and action callback threads. Also contains plot settings PlotState class."""

import operator
import webbrowser as wb
from functools import reduce
from typing import cast

import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
import vaex as vx
import xarray
from solara.lab import Menu, use_dark_effective, use_task

import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs._figurewidget import FigureWidget

from ...dataclass import Alert, State, SubsetState, use_subset, GridState
from ...util import check_catagorical
from .plot_settings import show_settings

# index context for grid
# NOTE: must be initialized here to avoid circular imports
index_context = sl.create_context(0)

# TEMPLATES AND STATE
# NOTE: all use standard vuetify grey colors
DARK_TEMPLATE = dict(layout=go.Layout(
    font=dict(color="white", size=16),
    showlegend=False,
    paper_bgcolor="#424242",  # darken-3
    autosize=True,
    plot_bgcolor="#212121",  # darken-4
    xaxis_gridcolor="#616161",  # darken-2
    yaxis_gridcolor="#616161",  # darken-2
    margin={
        "t": 30,
        "b": 80,
        "l": 80,
        "r": 80
    },
))
LIGHT_TEMPLATE = dict(layout=go.Layout(
    font=dict(color="black", size=16),
    showlegend=False,
    paper_bgcolor="#EEEEEE",  # lighten-3
    autosize=True,
    plot_bgcolor="#FAFAFA",  # lighten-5
    xaxis_gridcolor="#BDBDBD",  # lighten-1
    yaxis_gridcolor="#BDBDBD",  # lighten-1
    margin={
        "t": 30,
        "b": 80,
        "l": 80,
        "r": 80
    },
))


class PlotState:
    """
    Combination of reactive states which instantiate a specific plot's settings/properties
    """

    def __init__(self, plottype, current_key):
        # subset and type states
        self.plottype = str(plottype)
        # NOTE: this prevents a reactive update to override the initialization prop
        self.subset = sl.use_reactive(current_key)

        if 'table' in plottype:
            self.columns = sl.use_reactive(['g_mag', 'teff'])
        else:
            # common plot settings
            self.x = sl.use_reactive("teff")
            self.flipx = sl.use_reactive(False)
            self.flipy = sl.use_reactive(False)

            # moderately unique plot parameters/settings
            if plottype != "histogram":
                self.y = sl.use_reactive("logg")
                self.color = sl.use_reactive("fe_h")
                self.colorscale = sl.use_reactive("cividis")
            if plottype != "aggregated" and plottype != "skyplot":
                self.logx = sl.use_reactive(False)
                self.logy = sl.use_reactive(False)
            if plottype in ["scatter", "skyplot"]:
                self.colorlog = sl.use_reactive(cast(str, None))

            # statistics settings
            if plottype == "heatmap" or plottype == "histogram" or "delta" in plottype:
                self.nbins = sl.use_reactive(200)
                if plottype == "heatmap" or plottype == "delta2d":
                    self.bintype = sl.use_reactive("mean")
                    self.binscale = sl.use_reactive(None)
                else:
                    self.bintype = sl.use_reactive("count")
                    self.norm = sl.use_reactive(cast(str, None))

            # skyplot settings
            if plottype == "skyplot":
                self.geo_coords = sl.use_reactive("celestial")
                self.projection = sl.use_reactive("hammer")

            # delta view settings
            if "delta" in plottype:
                # NOTE: view can only be created when there are 2 subsets
                self.subset_b = sl.use_reactive(current_key)
            # all lookup data for plottypes
            # TODO: move this lookup data elsewhere to reduce the size of the plotstate objects
        self.Lookup = dict(
            norms=[
                None, "percent", "probability", "density",
                "probability density"
            ],
            bintypes=["count", "mean", "median", "sum", "min", "max", "mode"],
            colorscales=px.colors.named_colorscales(),
            binscales=[None, "log1p", "log10"],
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

    def swap_subsets(self):
        # saves current to p and q
        p = self.subset.value
        q = self.subset_b.value
        self.subset.value = q
        self.subset_b.value = p

    def reset_values(self):
        """Conditional reset based on if given column/subset is still in list"""
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

        # columnar resets for table
        if 'table' in self.plottype:
            for col in self.columns.value:
                if col not in State.columns.value:
                    # NOTE: i choose to remove quietly on stats table -- its very obvious when it disappears
                    self.columns.set(
                        list([q for q in self.columns.value if q != col]))
                    return

        # columnar resets for plots
        else:
            if self.x.value not in State.columns.value:
                Alert.update("VC removed! Column reset to 'teff'",
                             color="info")
                self.x.value = "teff"
            if self.plottype != "histogram":
                if self.y.value not in State.columns.value:
                    Alert.update("VC removed! Column reset to 'logg'",
                                 color="info")
                    self.y.value = "logg"
                if self.color.value not in State.columns.value:
                    Alert.update("VC removed! Column reset to 'fe_h'",
                                 color="info")
                    self.color.value = "fe_h"

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


def range_loop(start, offset):
    return (start + (offset % 360) + 360) % 360


def check_cat_color(color: vx.Expression) -> bool:
    """Helper function to check color expression with catagorical error check."""
    try:
        assert not check_catagorical(color)
    except AssertionError:
        Alert.update(
            "Discrete/catagorical color not supported. Please revert.",
            color="warning")
        return False
    return True


# SHOW PLOT
def show_plot(plottype, del_func):
    # NOTE: force set to grey darken-3 colour for visibility of card against grey darken-4 background
    dark = use_dark_effective()
    with rv.Card(
            class_="grey darken-3" if dark else "grey lighten-3",
            style_="width: 100%; height: 100%",
    ):
        # NOTE: current key has to be memoized outside the instantiation (why I couldn't tell you)
        current_key = sl.use_memo(
            lambda: list(SubsetState.subsets.value.keys())[-1],
            dependencies=[])
        print("SHOWPLOT KEY", current_key)
        plotstate = PlotState(plottype, current_key)
        with rv.CardText():
            with sl.Column(
                    classes=["grey darken-3" if dark else "grey lighten-3"]):
                if plottype == "histogram":
                    HistogramPlot(plotstate)
                elif plottype == "heatmap":
                    HeatmapPlot(plotstate)
                elif plottype == "scatter":
                    ScatterPlot(plotstate)
                elif plottype == "skyplot":
                    SkymapPlot(plotstate)
                elif plottype == "delta2d":
                    DeltaHeatmapPlot(plotstate)
                btn = sl.Button(
                    icon_name="mdi-settings",
                    outlined=False,
                    classes=["grey darken-3" if dark else "grey lighten-3"],
                )
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        show_settings(plottype, plotstate)
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=del_func,
                        )


@sl.component()
def ScatterPlot(plotstate):
    """Scattergl rendered scatter plot for single subset"""
    df: vx.DataFrame = State.df.value
    dark = use_dark_effective()
    filter, set_filter = use_subset(id(df), plotstate.subset, "scatter")
    relayout, set_relayout = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    use_task(update_grid, dependencies=[GridState.grid_layout.value])

    def update_filter():
        xfilter = None
        yfilter = None

        try:
            min = relayout["xaxis.range[0]"]
            max = relayout["xaxis.range[1]"]
            if plotstate.logx.value:
                min = 10**min
                max = 10**max
            xfilter = df[
                f"(({plotstate.x.value} > {np.min((min,max))}) & ({plotstate.x.value} < {np.max((min,max))}))"]
        except KeyError:
            pass
        try:
            min = relayout["yaxis.range[0]"]
            max = relayout["yaxis.range[1]"]
            if plotstate.logy.value:
                min = 10**min
                max = 10**max
            yfilter = df[
                f"(({plotstate.y.value} > {np.min((min,max))}) & ({plotstate.y.value} < {np.max((min,max))}))"]

        except KeyError:
            pass
        if xfilter is not None and yfilter is not None:
            filters = [xfilter, yfilter]
        else:
            filters = [xfilter if xfilter is not None else yfilter]
        filter = reduce(operator.and_, filters[1:], filters[0])
        set_local_filter(filter)

    use_task(update_filter, dependencies=[relayout])

    # Apply global and local filters
    if filter is not None:
        dff = df[filter]
    else:
        dff = df

    if local_filter is not None:
        dff = dff[local_filter]
    else:
        dff = dff

    if len(dff) > 20000:
        dff = dff[:20_000]

    def create_fig():
        x = dff[plotstate.x.value].values
        y = dff[plotstate.y.value].values
        c = dff[plotstate.color.value].values
        ids = dff["sdss_id"].values
        figure = go.Figure(
            data=go.Scattergl(
                x=x,
                y=y,
                mode="markers",
                customdata=ids,
                hovertemplate=f"<b>{plotstate.x.value}</b>:" +
                " %{x:.6f}<br>" + f"<b>{plotstate.y.value}</b>:" +
                " %{y:.6f}<br>" + f"<b>{plotstate.color.value}</b>:" +
                " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                " %{customdata:.d}",
                name="",
                marker=dict(
                    color=c,
                    colorbar=dict(title=plotstate.color.value),
                    colorscale=plotstate.colorscale.value,
                ),
            ),
            layout=go.Layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
                coloraxis=dict(
                    cmin=dff.min(plotstate.color.value)[()],
                    cmax=dff.max(plotstate.color.value)[()],
                ),
            ),
        )
        return figure

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    # Effect based callbacks (flip, log, & data array updates)
    def add_effects(fig_element: sl.Element):

        def add_context_menu():
            # TODO: except contextmenu in DOM somehow so i can open my own vue menu

            def on_click(trace, points, selector):
                # right click
                if selector.button == 2:
                    pass
                    # print(trace.customdata[points.point_inds[0]])
                elif selector.button == 0 and selector.shift:
                    # NOTE: binding is <Shift+LMB>
                    zora_url = (
                        "http://data.sdss5.org/zora"  # TODO: get zora url from ENVVAR
                    )
                    wb.open(
                        f"{zora_url}/target/{trace.customdata[points.point_inds[0]]}"
                    )

            fig_widget: FigureWidget = sl.get_widget(fig_element)
            points = fig_widget.data[0]
            points.on_click(on_click)

        sl.use_effect(add_context_menu, dependencies=[relayout])

        def set_xflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if fig_widget.layout.xaxis.range is not None:
                if plotstate.flipx.value:
                    fig_widget.update_xaxes(autorange="reversed")
                else:
                    fig_widget.update_xaxes(
                        range=fig_widget.layout.xaxis.range[::-1])

        def set_yflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if fig_widget.layout.yaxis.range is not None:
                if plotstate.flipy.value:
                    fig_widget.update_yaxes(autorange="reversed")
                else:
                    fig_widget.update_yaxes(
                        range=fig_widget.layout.yaxis.range[::-1])

        def set_log():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.logx.value:
                fig_widget.update_xaxes(type="log")
            else:
                fig_widget.update_xaxes(type="linear")
            if plotstate.logy.value:
                fig_widget.update_yaxes(type="log")
            else:
                fig_widget.update_yaxes(type="linear")

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_traces(
                x=dff[plotstate.x.value].values,
                y=dff[plotstate.y.value].values,
                customdata=dff["sdss_id"].values,
                hovertemplate=(f"<b>{plotstate.x.value}</b>:" +
                               " %{x:.6f}<br>" +
                               f"<b>{plotstate.y.value}</b>:" +
                               " %{y:.6f}<br>" +
                               f"<b>{plotstate.color.value}</b>:" +
                               " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                               " %{customdata:.d}"),
            )
            fig_widget.update_layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
            )

        def update_xy():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_traces(
                x=dff[plotstate.x.value].values,
                y=dff[plotstate.y.value].values,
                hovertemplate=(f"<b>{plotstate.x.value}</b>:" +
                               " %{x:.6f}<br>" +
                               f"<b>{plotstate.y.value}</b>:" +
                               " %{y:.6f}<br>" +
                               f"<b>{plotstate.color.value}</b>:" +
                               " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                               " %{customdata:.d}"),
            )
            fig_widget.update_layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
            )
            # check for axes flip and set accordingly to auto or reversed
            if fig_widget.layout.xaxis.range is not None:
                if plotstate.flipx.value:
                    fig_widget.update_xaxes(autorange="reversed")
                else:
                    fig_widget.update_xaxes(autorange=True)

            if fig_widget.layout.yaxis.range is not None:
                if plotstate.flipy.value:
                    fig_widget.update_yaxes(autorange="reversed")
                else:
                    fig_widget.update_yaxes(autorange=True)

        def update_color():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # error checker for color update
            if not check_cat_color(dff[plotstate.color.value]):
                return

            # scale by log if wanted
            c = dff[plotstate.color.value].values
            if plotstate.colorlog.value == "log1p":
                c = np.log1p(c)
            elif plotstate.colorlog.value == "log10":
                c = np.log10(c)

            fig_widget.update_traces(
                marker=dict(
                    color=c,
                    colorbar=dict(title=plotstate.color.value),
                    colorscale=plotstate.colorscale.value,
                ),
                hovertemplate=(f"<b>{plotstate.x.value}</b>:" +
                               " %{x:.6f}<br>" +
                               f"<b>{plotstate.y.value}</b>:" +
                               " %{y:.6f}<br>" +
                               f"<b>{plotstate.color.value}</b>:" +
                               " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                               " %{customdata:.d}"),
            )

        def update_layout():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(height=layout["h"] * 45 - 90)
            fig_widget.update_layout(width=layout["w"] * 120)

        sl.use_effect(update_layout, dependencies=[layout])

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE, )

        sl.use_effect(
            update_data,
            dependencies=[
                filter,
                local_filter,
            ],
        )
        sl.use_effect(
            update_color,
            dependencies=[
                filter,
                local_filter,
                plotstate.color.value,
                plotstate.colorscale.value,
                plotstate.colorlog.value,
            ],
        )
        sl.use_effect(update_xy,
                      dependencies=[plotstate.x.value, plotstate.y.value])
        sl.use_effect(set_xflip, dependencies=[plotstate.flipx.value])
        sl.use_effect(set_yflip, dependencies=[plotstate.flipy.value])
        sl.use_effect(update_theme, dependencies=[dark])
        sl.use_effect(
            set_log, dependencies=[plotstate.logx.value, plotstate.logy.value])

    # Plotly-side callbacks (relayout, select, and deselect)
    def on_relayout(data):
        if data is not None:
            # full limit reset, resetting relayout data + local filter
            if "xaxis.autorange" in data["relayout_data"].keys():
                set_relayout({})
                set_local_filter(None)
            # if change tool, skip update
            elif "dragmode" in data["relayout_data"].keys():
                return
            # Update the current dictionary
            else:
                set_relayout(dict(relayout, **data["relayout_data"]))

    def on_select(data):
        if len(data["points"]["xs"]) > 0:
            xs = data["points"]["xs"]
            ys = data["points"]["ys"]
            set_filter((df[plotstate.x.value].isin(xs) &
                        (df[plotstate.y.value].isin(ys))))

    def on_deselect(_data):
        set_filter(None)

    fig_el = sl.FigurePlotly(
        figure,
        on_selection=on_select,
        on_deselect=on_deselect,
        on_relayout=on_relayout,
        dependencies=[],
    )

    add_effects(fig_el)


@sl.component()
def HistogramPlot(plotstate):
    """Histogram plot for single subset"""
    df: vx.DataFrame = State.df.value
    xcol = plotstate.x.value
    nbins = plotstate.nbins.value
    filter, set_filter = use_subset(id(df), plotstate.subset, "histogram")
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})
    dark = use_dark_effective()

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.use_thread(update_grid, dependencies=[GridState.grid_layout.value])

    dff = df
    if filter:
        dff = df[filter]
    expr: vx.Expression = dff[xcol]

    def perform_binning():
        if check_catagorical(expr):
            # NOTE: under the hood, vaex uses pandas for this
            series = expr.value_counts()  # value_counts as in Pandas
            x = series.index.values
            y = series.values
            return x, y
        else:
            # check for length < 0
            try:
                assert len(dff) > 0
            except AssertionError:
                Alert.update("Applied filters reduced length to zero!",
                             color="warning")
                return None, None

            # get limits
            # INFO: can't be asynchronous; result is required
            try:
                limits = dff.minmax(xcol)
            except:
                Alert.update(
                    "Binning routine encountered stride bug, excepting...",
                    color="warning",
                )
                limits = [
                    # NOTE: empty tuple acts as index for the 0th of 0D array
                    dff.min(xcol)[()],
                    dff.max(xcol)[()],
                ]

            # make x (bin centers)
            # NOTE: no delay on this because it sucks
            x = dff.bin_centers(
                expression=expr,
                limits=limits,
                shape=nbins,
            )
            # create y (data) based on setting
            bintype = str(plotstate.bintype.value)
            if bintype == "count":
                y = dff.count(
                    binby=xcol,
                    limits=limits,
                    shape=nbins,
                    delay=True,
                )
            elif bintype == "sum":
                y = dff.sum(
                    expr,
                    binby=xcol,
                    limits=limits,
                    shape=nbins,
                    delay=True,
                )
            elif bintype == "mean":
                y = dff.mean(
                    expr,
                    binby=expr,
                    limits=limits,
                    shape=nbins,
                    delay=True,
                )
            elif bintype == "median":
                y = dff.median_approx(
                    expr,
                    binby=expr,
                    limits=limits,
                    shape=nbins,
                    delay=True,
                )

            elif bintype == "mode":
                y = dff.mode(
                    expression=expr,
                    binby=expr,
                    limits=limits,
                    shape=nbins,
                    delay=True,
                )
            elif bintype == "min":
                y = dff.min(
                    expression=expr,
                    binby=expr,
                    limits=limits,
                    shape=nbins,
                    array_type="xarray",
                    delay=True,
                )
            elif bintype == "max":
                y = dff.max(
                    expression=expr,
                    binby=expr,
                    limits=limits,
                    shape=nbins,
                    array_type="xarray",
                    delay=True,
                )
            else:
                raise ValueError("no assigned bintype for histogram.")
            df.execute()
            return x, y.get()

    if check_catagorical(expr):
        logx = False
    else:
        logx = plotstate.logx.value

    def create_fig():
        x, y = perform_binning()
        fig = px.histogram(
            x=x,
            y=y,
            nbins=nbins,
            log_x=logx,
            log_y=plotstate.logy.value,
            histnorm=plotstate.norm.value,
            labels={
                "x": xcol,
                "y": f"{plotstate.bintype.value}({xcol})",
            },
            template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
        )
        fig.update_yaxes(title="Frequency")
        fig.update_layout(margin_r=10)

        return fig

    # only instantiate the figure widget once.
    figure = sl.use_memo(create_fig, dependencies=[])

    # Effect based callbacks (flip, log, & data array updates)
    def add_effects(fig_element: sl.Element):

        def set_xflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if fig_widget.layout.xaxis.range is not None:
                if plotstate.flipx.value:
                    fig_widget.update_xaxes(autorange="reversed")
                else:
                    fig_widget.update_xaxes(
                        range=fig_widget.layout.xaxis.range[::-1])

        def set_yflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if fig_widget.layout.yaxis.range is not None:
                if plotstate.flipy.value:
                    fig_widget.update_yaxes(autorange="reversed")
                else:
                    fig_widget.update_yaxes(
                        range=fig_widget.layout.yaxis.range[::-1])

        def set_log():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.logx.value:
                fig_widget.update_xaxes(type="log")
            else:
                fig_widget.update_xaxes(type="linear")
            if plotstate.logy.value:
                fig_widget.update_yaxes(type="log")
            else:
                fig_widget.update_yaxes(type="linear")

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            x, y = perform_binning()

            fig_widget.update_traces(
                x=x,
                y=y,
                nbinsx=plotstate.nbins.value,
                hovertemplate=f"<b>{xcol}</b>:" + " %{x}<br>" +
                f"<b>{plotstate.bintype.value}({xcol})</b>:" + " %{y}<br>",
            )
            fig_widget.update_layout(
                xaxis_title=xcol,
                yaxis_title=f"{plotstate.bintype.value}({xcol})",
            )

        def update_layout():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(height=layout["h"] * 45 - 90)
            fig_widget.update_layout(width=layout["w"] * 120)

        sl.use_effect(update_layout, dependencies=[layout])

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE, )

        sl.use_effect(
            update_data,
            dependencies=[
                filter,
                xcol,
                plotstate.nbins.value,
                plotstate.bintype.value,
            ],
        )
        sl.use_effect(update_theme, dependencies=[dark])
        sl.use_effect(set_xflip, dependencies=[plotstate.flipx.value])
        sl.use_effect(set_yflip, dependencies=[plotstate.flipy.value])
        sl.use_effect(
            set_log, dependencies=[plotstate.logx.value, plotstate.logy.value])

    def on_select(data):
        if len(data["points"]["xs"]) > 0:
            filters = list()
            uniques = np.unique(data["points"]["xs"])
            binsize = uniques[1] - uniques[0]
            for cent in uniques:
                filters.append(df[f"({xcol} <= {cent + binsize})"]
                               & df[f"({xcol} >= {cent - binsize})"])
            filters = reduce(operator.or_, filters[1:], filters[0])
            set_filter(filters)

    def on_deselect(_data):
        set_filter(None)

    fig_el = sl.FigurePlotly(
        figure,
        on_selection=on_select,
        on_deselect=on_deselect,
        dependencies=[],
    )
    add_effects(fig_el)
    return fig_el


@sl.component()
def HeatmapPlot(plotstate):
    """2D Histogram plot (Heatmap) for single subset"""
    df = State.df.value
    filter, set_filter = use_subset(id(df), plotstate.subset,
                                    "filter-aggregated")
    dark = use_dark_effective()
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.use_thread(update_grid, dependencies=[GridState.grid_layout.value])

    dff = df
    if filter:
        dff = df[filter]

    def perform_binning():
        expr = (dff[plotstate.x.value], dff[plotstate.y.value])
        expr_c = dff[plotstate.color.value]
        bintype = str(plotstate.bintype.value)

        # error checking
        try:
            assert (
                len(dff)
                > 40), "0"  # NOTE: trial and error found this value. arbitrary
            assert plotstate.x.value != plotstate.y.value, "1"

            assert not check_catagorical(dff[plotstate.x.value]), "2"
            assert not check_catagorical(dff[plotstate.y.value]), "2"
        except AssertionError as e:
            msg = str(e)

            # length checks
            if msg == "0":
                Alert.update(
                    "Dataset too small to bin via aggregated. Use scatter view!",
                    color="warning",
                )
                # generate a flat xarray
                y = xarray.DataArray(
                    [[0, 0], [0, 0]],
                    coords={
                        plotstate.x.value: [0, 1],
                        plotstate.y.value: [0, 1],
                    },
                )
                return (y, 0, 1)
            elif msg == "1":
                # NOTE: for autoswap
                pass
            elif msg == "2":
                Alert.update(
                    "Catagorical data column set for aggregated -- not yet implemented! Not updating.",
                    color="error",
                )

            return (None, None, None)

        # TODO: report weird stride bug that occurs on this code

        try:
            limits = [
                dff.minmax(plotstate.x.value),
                dff.minmax(plotstate.y.value),
            ]
        except:
            Alert.update(
                "Binning routine encountered stride bug, excepting...",
                color="warning",
            )
            # NOTE: empty tuple acts as index for the 0th of 0D array
            limits = [
                [
                    dff.min(plotstate.x.value)[()],
                    dff.max(plotstate.x.value)[()],
                ],
                [
                    dff.min(plotstate.y.value)[()],
                    dff.max(plotstate.y.value)[()],
                ],
            ]

        if bintype == "count":
            y = dff.count(
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
                delay=True,
            )
        elif bintype == "sum":
            y = dff.sum(
                expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
                delay=True,
            )
        elif bintype == "mean":
            y = dff.mean(
                expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
                delay=True,
            )
        elif bintype == "median":
            y = dff.median_approx(
                expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                delay=True,
            )

        elif bintype == "mode":
            y = dff.mode(
                expression=expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                delay=True,
            )
        elif bintype == "min":
            y = dff.min(
                expression=expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
                delay=True,
            )
        elif bintype == "max":
            y = dff.max(
                expression=expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
                delay=True,
            )
        else:
            raise ValueError("no assigned bintype for aggregated")
        df.execute()
        y = y.get()
        if bintype == "median":
            # convert to xarray
            y = xarray.DataArray(
                y,
                coords={
                    plotstate.x.value:
                    dff.bin_centers(
                        expression=expr[0],
                        limits=limits[0],
                        shape=plotstate.nbins.value,
                    ),
                    plotstate.y.value:
                    dff.bin_centers(
                        expression=expr[1],
                        limits=limits[1],
                        shape=plotstate.nbins.value,
                    ),
                },
            )

        binscale = str(plotstate.binscale.value)
        if binscale == "log1p":
            y = np.log1p(y)
        elif binscale == "log10":
            y = np.log10(y)

        # TODO: clean this code
        y = y.where(np.abs(y) != np.inf, np.nan)
        cmin = float(np.min(y).values)
        cmax = float(np.max(y).values)
        y = y.fillna(-999)
        return y, cmin, cmax

    def set_colorlabel():
        if plotstate.bintype.value == "count":
            return f"count ({plotstate.binscale.value})"
        else:
            return f"{plotstate.color.value} ({plotstate.bintype.value})"

    def create_fig():
        z, cmin, cmax = perform_binning()
        colorlabel = set_colorlabel()
        fig = px.imshow(
            z.T,
            zmin=cmin,
            zmax=cmax,
            origin="lower",
            color_continuous_scale=plotstate.colorscale.value,
            labels={
                "x": plotstate.x.value,
                "y": plotstate.y.value,
                "color": colorlabel,
            },
            template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
        )
        return fig

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    def add_effects(fig_element: sl.Element):

        def set_xflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)

        def set_yflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=False)
                fig_widget.update_yaxes(autorange=True)

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # error checker for color update
            if not check_cat_color(dff[plotstate.color.value]):
                return

            # update data information
            z, cmin, cmax = perform_binning()
            if z is None:
                # TODO: in binning func return snackbar error based on check failure
                return

            colorlabel = set_colorlabel()

            # update data
            fig_widget.update_traces(
                z=z.T.data,
                x=z.coords[plotstate.x.value],
                y=z.coords[plotstate.y.value],
                hovertemplate=(f"{plotstate.x.value}" + ": %{x}<br>" +
                               f"{plotstate.y.value}:" + " %{y}<br>" +
                               f"{colorlabel}: " + "%{z}<extra></extra>"),
            )
            # update coloraxis & label information
            fig_widget.update_coloraxes(
                cmax=cmax,
                cmin=cmin,
                colorbar=dict(title=colorlabel),
                colorscale=plotstate.colorscale.value,
            )
            fig_widget.update_layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
            )

        def update_color():
            # NOTE: only for updating colorscale, since any other change
            # requires an entire plot change
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update coloraxis information
            fig_widget.update_coloraxes(
                colorscale=plotstate.colorscale.value, )

        def update_layout():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(height=layout["h"] * 45 - 90)
            fig_widget.update_layout(width=layout["w"] * 120)

        sl.use_effect(update_layout, dependencies=[layout])

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE)

        sl.use_effect(
            update_data,
            dependencies=[
                filter,
                plotstate.x.value,
                plotstate.y.value,
                plotstate.color.value,
                plotstate.bintype.value,
                plotstate.binscale.value,
                plotstate.nbins.value,
            ],
        )
        sl.use_effect(
            update_color,
            dependencies=[
                plotstate.colorscale.value,
            ],
        )
        sl.use_effect(update_theme, dependencies=[dark])
        sl.use_effect(set_xflip, dependencies=[plotstate.flipx.value])
        sl.use_effect(set_yflip, dependencies=[plotstate.flipy.value])

    fig_el = sl.FigurePlotly(figure)
    add_effects(fig_el)

    return


@sl.component()
def SkymapPlot(plotstate):
    """Sky projection plot of stars for a single subset."""
    df = State.df.value
    filter, set_filter = use_subset(id(df), plotstate.subset, "filter-skyplot")
    dark = use_dark_effective()
    relayout, set_relayout = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.use_thread(update_grid, dependencies=[GridState.grid_layout.value])

    def update_filter():
        if plotstate.geo_coords.value == "celestial":
            lon, lat = ("ra", "dec")
        else:
            lon, lat = ("l", "b")
        try:
            scale = relayout["geo.projection.scale"]
            if scale < 1.0:
                return
        except KeyError:
            scale = 1.0
        try:
            lon_center = relayout["geo.center.lon"]
        except KeyError:
            lon_center = 0
        try:
            lat_center = relayout["geo.center.lat"]
        except KeyError:
            lat_center = 0

        lonlow, lonhigh = (
            range_loop(0, -180 / scale + lon_center),
            range_loop(0, 180 / scale + lon_center),
        )
        latlow, lathigh = (
            np.max((lat_center - (90 / scale), -90)),
            np.min((lat_center + (90 / scale), 90)),
        )

        lonfilter = None
        if scale > 1:
            if lonhigh < lonlow:
                lonfilter = df[f"({lon} > {lonlow})"] | df[
                    f"({lon} < {lonhigh})"]
            else:
                lonfilter = df[f"({lon} > {lonlow})"] & df[
                    f"({lon} < {lonhigh})"]
        if lonfilter is not None:
            set_local_filter((df[f"({lat} > {latlow})"]
                              & df[f"({lat}< {lathigh})"]) & lonfilter)
        else:
            set_local_filter(df[f"({lat} > {latlow})"]
                             & df[f"({lat}< {lathigh})"])

    sl.use_thread(update_filter,
                  dependencies=[plotstate.geo_coords.value, relayout])

    # Apply global and local filters
    if filter is not None:
        dff = df[filter]
    else:
        dff = df

    if local_filter is not None:
        dff = dff[local_filter]
    else:
        dff = dff

    # cut dff to renderable length
    if len(dff) > 3000:
        dff = dff[:3_000]

    def create_fig():
        dtick = 30  # for tickers

        # always initialized as RA/DEC
        lon = dff["ra"].values
        lat = dff["dec"].values
        c = dff[plotstate.color.value].values
        ids = dff["sdss_id"].values

        figure = go.Figure(
            data=go.Scattergeo(
                lat=lat,
                lon=lon,
                mode="markers",
                customdata=ids,
                hovertemplate="<b>RA</b>:" + " %{lon:.6f}<br>" +
                "<b>DEC</b>:" + " %{lat:.6f}<br>" +
                f"<b>{plotstate.color.value}</b>:" +
                " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                " %{customdata:.d}",
                name="",
                marker=dict(
                    color=c,
                    colorbar=dict(title=plotstate.color.value),
                    colorscale=plotstate.colorscale.value,
                ),
            ),
            layout=go.Layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
                coloraxis=dict(
                    cmin=dff.min(plotstate.color.value)[()],
                    cmax=dff.max(plotstate.color.value)[()],
                ),
                geo=dict(
                    bgcolor="#212121",
                    projection_type=plotstate.projection.value,
                    visible=False,
                    lonaxis_showgrid=True,
                    lonaxis_gridcolor="#616161",
                    lonaxis_tick0=0,
                    lataxis_showgrid=True,
                    lataxis_gridcolor="#616161",
                    lataxis_tick0=0,
                ),
            ),
        )
        # axes markers
        dtick = 30
        x = list(range(0, 360, dtick))
        y = list(range(-90, 90 + dtick, dtick))
        xpos = 0
        ypos = 0
        figure.add_trace(
            go.Scattergeo({
                "lon": x + [xpos] * (len(y)),
                "lat": [ypos] * (len(x)) + y,
                "showlegend": False,
                "text": x + y,
                "mode": "text",
                "hoverinfo": "skip",
                "name": "text",
            }))
        figure.update_layout(margin={"t": 30, "b": 10, "l": 0, "r": 0})
        return figure

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    # Effect based callbacks (flip, log, & data array updates)
    def add_effects(fig_element: sl.Element):

        def set_flip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=True)

        def set_log():
            # log is meaningless on the projected skyplots
            pass

        def update_projection():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_geos(projection_type=plotstate.projection.value)

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update main trace
            if plotstate.geo_coords.value == "celestial":
                lon = "ra"
                lat = "dec"
            else:
                lon = "l"
                lat = "b"

            fig_widget.update_traces(
                lon=dff[lon].values,
                lat=dff[lat].values,
                customdata=dff["sdss_id"].values,
                selector=dict(type="scattergeo", name=""),
            )

        def update_color():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # error checker for color update
            if not check_cat_color(dff[plotstate.color.value]):
                return

            # scale by log if wanted
            c = dff[plotstate.color.value].values
            if plotstate.colorlog.value == "log1p":
                c = np.log1p(c)
            elif plotstate.colorlog.value == "log10":
                c = np.log10(c)

            # update main trace
            fig_widget.update_traces(
                marker=dict(
                    color=c,
                    colorbar=dict(title=plotstate.color.value),
                    colorscale=plotstate.colorscale.value,
                ),
                hovertemplate=
                (f"<b>{'RA' if plotstate.geo_coords.value == 'celestial' else 'l'}</b>:"
                 + " %{lon:.6f}<br>" +
                 f"<b>{'DEC' if plotstate.geo_coords.value == 'celestial' else 'b'}</b>:"
                 + " %{lat:.6f}<br>" + f"<b>{plotstate.color.value}</b>:" +
                 " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                 " %{customdata:.d}"),
                selector=dict(type="scattergeo", name=""),
            )

        def update_layout():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(height=layout["h"] * 45 - 90)
            fig_widget.update_layout(width=layout["w"] * 120)

        sl.use_effect(update_layout, dependencies=[layout])

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE)
            fig_widget.update_geos(
                bgcolor="#212121" if dark else "#FAFAFA",
                lonaxis_gridcolor="#616161" if dark else "#BDBDBD",
                lataxis_gridcolor="#616161" if dark else "#BDBDBD",
            )

        sl.use_effect(
            update_data,
            dependencies=[filter, local_filter, plotstate.geo_coords.value])
        sl.use_effect(update_projection,
                      dependencies=[plotstate.projection.value])
        sl.use_effect(
            update_color,
            dependencies=[
                filter,
                local_filter,
                plotstate.color.value,
                plotstate.colorscale.value,
                plotstate.colorlog.value,
            ],
        )
        sl.use_effect(
            set_flip,
            dependencies=[plotstate.flipx.value, plotstate.flipy.value])
        sl.use_effect(update_theme, dependencies=[dark])

    # Plotly-side callbacks (relayout, select, deselect)
    def on_relayout(data):
        if data is not None:
            # full limit reset, resetting relayout data + local filter
            if "geo.fitbounds" in data["relayout_data"].keys():
                set_relayout({})
                set_local_filter(None)
            # if change tool, skip update
            elif "dragmode" in data["relayout_data"].keys():
                pass
            # Update the current dictionary
            else:
                set_relayout(dict(relayout, **data["relayout_data"]))

    def on_select(data):
        if len(data["points"]["xs"]) > 0:
            bool_arr = np.array(data["points"]["trace_indexes"]) == 0
            print(np.array(data["points"]["point_indexes"])[bool_arr])

            # set_filter(df[df == dff[data["points"]["point_indexes"]]])

    def on_deselect(_data):
        set_filter(None)

    fig_el = sl.FigurePlotly(
        figure,
        # on_selection=on_select,
        # on_deselect=on_deselect,
        on_relayout=on_relayout,
        dependencies=[],
    )
    add_effects(fig_el)
    return fig_el


@sl.component()
def DeltaHeatmapPlot(plotstate):
    """Heatmap on regular grid for Subset A - Subset B"""
    df = State.df.value
    filterA, set_filterA = use_subset(id(df), plotstate.subset, "delta2d")
    filterB, set_filterB = use_subset(id(df), plotstate.subset_b, "delta2d")
    dark = use_dark_effective()
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state(GridState.grid_layout.value[0])

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.use_thread(update_grid, dependencies=[GridState.grid_layout.value])

    if filterA:
        dfa = df[filterA]
    else:
        dfa = df
    if filterB:
        dfb = df[filterB]
    else:
        dfb = df

    def perform_binning():
        # create limits

        # the limits/grid must be of an identical size, so we MUST use the same limits
        # for both dataframes
        try:
            limits = [
                dfa.minmax(plotstate.x.value),
                dfa.minmax(plotstate.y.value),
            ]
        except:
            Alert.update(
                "Binning routine encountered stride bug, excepting...",
                color="warning",
            )
            # NOTE: empty tuple acts as index for the 0th of 0D array
            limits = [
                [
                    dfa.min(plotstate.x.value)[()],
                    dfa.max(plotstate.x.value)[()],
                ],
                [
                    dfa.min(plotstate.y.value)[()],
                    dfa.max(plotstate.y.value)[()],
                ],
            ]

        q = list()  # list for z nD promises

        # iterate through
        for dff in (dfa, dfb):
            expr = (dff[plotstate.x.value], dff[plotstate.y.value])
            expr_c = dff[plotstate.color.value]
            bintype = str(plotstate.bintype.value)

            # error checking
            try:
                assert (
                    len(dff) > 40
                ), "0"  # NOTE: trial and error found this value. arbitrary
                assert plotstate.x.value != plotstate.y.value, "1"
                assert len(SubsetState.subsets.value) != 1, "3"
                assert plotstate.subset.value != plotstate.subset_b.value, "1"

                assert not check_catagorical(dff[plotstate.x.value]), "2"
                assert not check_catagorical(dff[plotstate.y.value]), "2"
            except AssertionError as e:
                msg = str(e)

                # length checks
                if msg == "0":
                    Alert.update(
                        "Subset too small to bin via aggregated. Use scatter view!",
                        color="warning",
                    )
                    # generate a flat xarray
                    y = xarray.DataArray(
                        [[0, 0], [0, 0]],
                        coords={
                            plotstate.x.value: [0, 1],
                            plotstate.y.value: [0, 1],
                        },
                    )
                    return (y, 0, 1)
                elif msg == "1":
                    # NOTE: for autoswaps
                    pass
                elif msg == "2":
                    Alert.update(
                        "Catagorical data column set for aggregated -- not yet implemented! Not updating.",
                        color="error",
                    )
                elif msg == "3":
                    Alert.update(
                        "Delta view is only informative with 2 subsets. Please create another subset to compare against.",
                        color="info",
                    )

                return (None, None, None)

            if bintype == "count":
                y = dff.count(
                    binby=expr,
                    limits=limits,
                    shape=plotstate.nbins.value,
                    array_type="xarray",
                    delay=True,
                )
            elif bintype == "sum":
                y = dff.sum(
                    expr_c,
                    binby=expr,
                    limits=limits,
                    shape=plotstate.nbins.value,
                    array_type="xarray",
                    delay=True,
                )
            elif bintype == "mean":
                y = dff.mean(
                    expr_c,
                    binby=expr,
                    limits=limits,
                    shape=plotstate.nbins.value,
                    array_type="xarray",
                    delay=True,
                )
            elif bintype == "median":
                # y = dff.median_approx(
                #    expr_c,
                #    binby=expr,
                #    limits=limits,
                #    shape=plotstate.nbins.value,
                #    delay=True,
                # )
                # generate a flat xarray
                y = xarray.DataArray(
                    [[0, 0], [0, 0]],
                    coords={
                        plotstate.x.value: [0, 1],
                        plotstate.y.value: [0, 1],
                    },
                )
                return (y, 0, 1)

            elif bintype == "mode":
                y = dff.mode(
                    expression=expr_c,
                    binby=expr,
                    limits=limits,
                    shape=plotstate.nbins.value,
                    delay=True,
                )
            elif bintype == "min":
                y = dff.min(
                    expression=expr_c,
                    binby=expr,
                    limits=limits,
                    shape=plotstate.nbins.value,
                    array_type="xarray",
                    delay=True,
                )
            elif bintype == "max":
                y = dff.max(
                    expression=expr_c,
                    binby=expr,
                    limits=limits,
                    shape=plotstate.nbins.value,
                    array_type="xarray",
                    delay=True,
                )
            else:
                raise ValueError("no assigned bintype for aggregated")
            q.append(y)

        df.execute()  # run all promises

        for i, y in enumerate(q):
            y = y.get()  # fetch numerical promise value
            if bintype == "median":
                # convert to xarray
                if i == 0:
                    dff = dfa
                else:
                    dff = dfb
                expr = (dff[plotstate.x.value], dff[plotstate.y.value])

                y = xarray.DataArray(
                    y,
                    coords={
                        plotstate.x.value:
                        dff.bin_centers(
                            expression=expr[0],
                            limits=limits[0],
                            shape=plotstate.nbins.value,
                        ),
                        plotstate.y.value:
                        dff.bin_centers(
                            expression=expr[1],
                            limits=limits[1],
                            shape=plotstate.nbins.value,
                        ),
                    },
                )
            q[i] = y

        y = q[0] - q[1]  # get differences

        binscale = str(plotstate.binscale.value)
        if binscale == "log1p":
            y = np.log1p(y)
        elif binscale == "log10":
            y = np.log10(y)

        # TODO: clean this code
        y = y.where(np.abs(y) != np.inf, np.nan)
        cmin = float(np.min(y).values)
        cmax = float(np.max(y).values)
        y = y.fillna(-999)
        return y, cmin, cmax

    def set_colorlabel():
        if plotstate.bintype.value == "count":
            return f"Delta count ({plotstate.binscale.value})"
        else:
            return f"Delta {plotstate.color.value} ({plotstate.bintype.value})"

    def create_fig():
        z, cmin, cmax = perform_binning()
        colorlabel = set_colorlabel()
        fig = px.imshow(
            z.T,
            zmin=cmin,
            zmax=cmax,
            origin="lower",
            color_continuous_scale=plotstate.colorscale.value,
            labels={
                "x": plotstate.x.value,
                "y": plotstate.y.value,
                "color": colorlabel,
            },
            template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
        )
        return fig

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    def add_effects(fig_element: sl.Element):

        def set_xflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)

        def set_yflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=False)
                fig_widget.update_yaxes(autorange=True)

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # error checker for color update
            if not check_cat_color(dfa[plotstate.color.value]):
                return
            if not check_cat_color(dfb[plotstate.color.value]):
                return

            # update data information
            z, cmin, cmax = perform_binning()
            if z is None:
                # TODO: in binning func return snackbar error based on check failure
                return

            colorlabel = set_colorlabel()

            # update data
            fig_widget.update_traces(
                z=z.T.data,
                x=z.coords[plotstate.x.value],
                y=z.coords[plotstate.y.value],
                hovertemplate=(f"{plotstate.x.value}" + ": %{x}<br>" +
                               f"{plotstate.y.value}:" + " %{y}<br>" +
                               f"{colorlabel}: " + "%{z}<extra></extra>"),
            )
            # update coloraxis & label information
            fig_widget.update_coloraxes(
                cmax=cmax,
                cmin=cmin,
                colorbar=dict(title=colorlabel),
                colorscale=plotstate.colorscale.value,
            )
            fig_widget.update_layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
            )

        def update_color():
            # NOTE: only for updating colorscale, since any other change
            # requires an entire plot change
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update coloraxis information
            fig_widget.update_coloraxes(
                colorscale=plotstate.colorscale.value, )

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE)

        sl.use_effect(
            update_data,
            dependencies=[
                filterA,
                filterB,
                plotstate.x.value,
                plotstate.y.value,
                plotstate.color.value,
                plotstate.bintype.value,
                plotstate.binscale.value,
                plotstate.nbins.value,
            ],
        )
        sl.use_effect(
            update_color,
            dependencies=[
                plotstate.colorscale.value,
            ],
        )

        def update_layout():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(height=layout["h"] * 45 - 90)
            fig_widget.update_layout(width=layout["w"] * 120)

        sl.use_effect(update_layout, dependencies=[layout])
        sl.use_effect(update_theme, dependencies=[dark])
        sl.use_effect(set_xflip, dependencies=[plotstate.flipx.value])
        sl.use_effect(set_yflip, dependencies=[plotstate.flipy.value])

    fig_el = sl.FigurePlotly(figure)
    add_effects(fig_el)

    return
