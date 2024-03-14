import copy
import operator
from functools import reduce
from typing import cast

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import reacton.ipyvuetify as rv
import solara as sl
import vaex as vx
import xarray
from plotly.graph_objs._figurewidget import FigureWidget
from solara.components.card import Card
from solara.components.columns import Columns
from solara.lab import Menu, ContextMenu, use_dark_effective

from state import State
from util import check_catagorical

# TEMPLATES AND STATE
DARK_TEMPLATE = dict(layout=go.Layout(
    font=dict(color="white", size=16),
    showlegend=False,
    paper_bgcolor="#424242",
    autosize=True,
    plot_bgcolor="#212121",
    xaxis_gridcolor="#616161",
    yaxis_gridcolor="#616161",
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
    paper_bgcolor="#EEEEEE",
    autosize=True,
    plot_bgcolor="#FAFAFA",
    xaxis_gridcolor="#BDBDBD",
    yaxis_gridcolor="#BDBDBD",
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

    def __init__(self, type):
        # common settings
        self.x = sl.use_reactive("teff")
        self.flipx = sl.use_reactive(False)
        self.flipy = sl.use_reactive(False)

        # moderately unique plot parameters/settings
        if type != "histogram":
            self.y = sl.use_reactive("logg")
            self.color = sl.use_reactive("fe_h")
            self.colorscale = sl.use_reactive("viridis")
        if type != "aggregated" and type != "skyplot":
            self.logx = sl.use_reactive(False)
            self.logy = sl.use_reactive(False)

        # statistics settings
        if type == "aggregated" or type == "histogram":
            self.nbins = sl.use_reactive(200)
            if type == "aggregated":
                self.bintype = sl.use_reactive("mean")
                self.binscale = sl.use_reactive(None)
            else:
                self.norm = sl.use_reactive(cast(str, None))

        # skyplot settings
        if type == "skyplot":
            self.geo_coords = sl.use_reactive("celestial")
            self.projection = sl.use_reactive("hammer")

        # all lookup data for types
        # TODO: move this lookup data elsewhere to reduce the size of the plotstate objects
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


def range_loop(start, offset):
    return (start + (offset % 360) + 360) % 360


# SHOW PLOT
def show_plot(type, del_func):
    with rv.Card(class_="grey darken-3", style_="width: 100%; height: 100%"):
        plotstate = PlotState(type)
        with rv.CardText():
            with sl.Column(classes=["grey darken-3"]):
                if type == "histogram":
                    histogram(plotstate)
                elif type == "aggregated":
                    aggregated(plotstate)
                elif type == "scatter":
                    # scatterplot()
                    scatter(plotstate)
                elif type == "skyplot":
                    skyplot(plotstate)
                btn = sl.Button(icon_name="mdi-settings",
                                outlined=False,
                                classes=["grey darken-3"])
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        show_settings(type, plotstate)
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=del_func,
                        )


@sl.component
def scatter(plotstate):
    df: vx.DataFrame = State.df.value
    dark = use_dark_effective()
    filter, set_filter = sl.use_cross_filter(id(df), "scatter")
    relayout, set_relayout = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)

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

    sl.use_thread(update_filter, dependencies=[relayout])

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
                    cmin=np.float32(dff.min(plotstate.color.value)),
                    cmax=np.float32(dff.max(plotstate.color.value)),
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
                if selector.button == 2:
                    print(trace.customdata[points.point_inds[0]])

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
            data = fig_widget.data[0]
            data.x = dff[plotstate.x.value].values
            data.y = dff[plotstate.y.value].values
            data.customdata = dff["sdss_id"].values
            data.marker = dict(
                color=dff[plotstate.color.value].values,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            )
            data.hovertemplate = (f"<b>{plotstate.x.value}</b>:" +
                                  " %{x:.6f}<br>" +
                                  f"<b>{plotstate.y.value}</b>:" +
                                  " %{y:.6f}<br>" +
                                  f"<b>{plotstate.color.value}</b>:" +
                                  " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                                  " %{customdata:.d}")
            fig_widget.update_layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
            )

        def update_color():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update main trace
            data = fig_widget.data[0]
            data.marker = dict(
                color=dff[plotstate.color.value].values,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            )
            data.hovertemplate = (f"<b>{plotstate.x.value}</b>:" +
                                  " %{x:.6f}<br>" +
                                  f"<b>{plotstate.y.value}</b>:" +
                                  " %{y:.6f}<br>" +
                                  f"<b>{plotstate.color.value}</b>:" +
                                  " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                                  " %{customdata:.d}")

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE)

        sl.use_effect(
            update_data,
            dependencies=[
                filter,
                local_filter,
                plotstate.x.value,
                plotstate.y.value,
            ],
        )
        sl.use_effect(
            update_color,
            dependencies=[plotstate.color.value, plotstate.colorscale.value],
        )
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
                pass
            # Update the current dictionary
            else:
                set_relayout(dict(relayout, **data["relayout_data"]))

    def on_select(data):
        if len(data["points"]["xs"]) > 0:
            set_filter((df[plotstate.x.value].isin(data["points"]["xs"])
                        & (df[plotstate.y.value].isin(data["points"]["ys"]))))

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


@sl.component
def histogram(plotstate):
    df: vx.DataFrame = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "histogram")
    dark = use_dark_effective()

    dff = df
    if filter:
        dff = df[filter]
    expr: vx.Expression = dff[plotstate.x.value]

    def perform_binning():
        if check_catagorical(expr):
            x = expr.unique()
            y = []
            for i in x:
                # TODO: raise issue about vaex being unable to count catagorical data
                y.append(float(expr.str.count(i).sum()))
        else:
            # make x (bin centers) and y (counts)
            # TODO: raise issue about stride bug on value change
            x = dff.bin_centers(
                expression=expr,
                limits=dff.minmax(plotstate.x.value),
                shape=plotstate.nbins.value,
            )
            y = dff.count(
                binby=plotstate.x.value,
                limits=dff.minmax(plotstate.x.value),
                shape=plotstate.nbins.value,
            )
        return x, y

    if check_catagorical(expr):
        logx = False
    else:
        logx = plotstate.logx.value

    def create_fig():
        x, y = perform_binning()
        fig = px.histogram(
            x=x,
            y=y,
            nbins=plotstate.nbins.value,
            log_x=logx,
            log_y=plotstate.logy.value,
            histnorm=plotstate.norm.value,
            labels={
                "x": plotstate.x.value,
            },
            template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
        )
        fig.update_yaxes(title="Frequency")
        fig.update_layout(margin_r=10)

        return fig

    # only instantiate the figure widget once
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
            data = fig_widget.data[0]
            data.x, data.y = perform_binning()
            fig_widget.update_layout(xaxis_title=plotstate.x.value, )

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE)

        sl.use_effect(
            update_data,
            dependencies=[
                filter,
                plotstate.x.value,
                plotstate.nbins.value,
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
            binsize = data["points"]["xs"][1] - data["points"]["xs"][0]
            for cent in np.unique(data["points"]["xs"]):
                filters.append(
                    df[f"({plotstate.x.value} <= {cent + binsize})"]
                    & df[f"({plotstate.x.value} >= {cent - binsize})"])
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


@sl.component
def aggregated(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-aggregated")
    dark = use_dark_effective()

    dff = df
    if filter:
        dff = df[filter]

    x_cat = check_catagorical(dff[plotstate.x.value])
    y_cat = check_catagorical(dff[plotstate.y.value])
    if x_cat or y_cat:
        # TODO: move this to inside the data update, making the error message as a temporary popup
        return sl.Warning(
            icon=True,
            label=
            "Selected columns are catagorical! Incompatible with aggregated plot.",
        )

    def perform_binning():
        expr = (dff[plotstate.x.value], dff[plotstate.y.value])
        expr_c = dff[plotstate.color.value]
        bintype = str(plotstate.bintype.value)

        # TODO: report weird stride bug that occurs on this commented code
        # xlims, set_xlims = sl.use_state(None)
        # ylims, set_ylims = sl.use_state(None)
        # if xlims is None and ylims is None:
        #    limits = [dff.minmax(plotstate.x.value), dff.minmax(plotstate.y.value)]
        # else:
        #    limits = [xlims, ylims]
        limits = [dff.minmax(plotstate.x.value), dff.minmax(plotstate.y.value)]

        if bintype == "count":
            y = dff.count(
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
            )
        elif bintype == "mean":
            y = dff.mean(
                expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
            )
        elif bintype == "median":
            # NOTE: i can convert the numpy out into an xarray, should work fine
            y = dff.median_approx(
                expr_c,
                binby=expr,
                shape=plotstate.nbins.value,
            )
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

        elif bintype == "mode":
            y = dff.mode(
                expression=expr,
                binby=[expr_x, expr_y],
                limits=[
                    dff.minmax(plotstate.x.value),
                    dff.minmax(plotstate.y.value)
                ],
                shape=plotstate.nbins.value,
            )
        elif bintype == "min":
            y = dff.min(
                expression=expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
            )
        elif bintype == "max":
            y = dff.max(
                expression=expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
            )
        else:
            raise ValueError("no assigned bintype for aggregated")

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
            print(fig_widget.layout.xaxis)

        def set_yflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=False)
                fig_widget.update_yaxes(autorange=True)
            print(fig_widget.layout.yaxis)

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update data information
            z, cmin, cmax = perform_binning()
            colorlabel = set_colorlabel()
            data = fig_widget.data[0]
            data.z = z.T.data
            data.x = z.coords[plotstate.x.value]
            data.y = z.coords[plotstate.y.value]
            data.hovertemplate = (f"{plotstate.x.value}" + ": %{x}<br>" +
                                  f"{plotstate.y.value}:" + " %{y}<br>" +
                                  f"{colorlabel}: " + "%{z}<extra></extra>")

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


@sl.component
def skyplot(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(
        id(df), "skyplot"
    )  # TODO: check if filters interfere because they have the same ID
    dark = use_dark_effective()
    relayout, set_relayout = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)

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

    sl.use_thread(update_filter, dependencies=[relayout])

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
    dff = dff[:3_000]

    def create_fig():
        dtick = 30  # for tickers

        # always initialized as RA/DEC
        lon = dff["ra"]
        lat = dff["dec"]
        c = dff[plotstate.color.value]
        ids = dff["sdss_id"]

        figure = go.Figure(
            data=go.Scattergeo(
                lat=lat.values,
                lon=lon.values,
                mode="markers",
                customdata=ids.values,
                hovertemplate="<b>RA</b>:" + " %{lon:.6f}<br>" +
                "<b>DEC</b>:" + " %{lat:.6f}<br>" +
                f"<b>{plotstate.color.value}</b>:" +
                " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                " %{customdata:.d}",
                name="",
                marker=dict(
                    color=c.values,
                    colorbar=dict(title=plotstate.color.value),
                    colorscale=plotstate.colorscale.value,
                ),
            ),
            layout=go.Layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE,
                coloraxis=dict(
                    cmin=np.float32(dff.min(plotstate.color.value)),
                    cmax=np.float32(dff.max(plotstate.color.value)),
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
        x = list(range(0, 360 + dtick, dtick))
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

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update main trace
            data = fig_widget.data[0]
            if plotstate.geo_coords.value == "celestial":
                data.lon = dff["ra"].values
                data.lat = dff["dec"].values
            else:
                data.lon = dff["l"].values
                data.lat = dff["b"].values
            data.customdata = dff["sdss_id"].values
            data.marker = dict(
                color=dff[plotstate.color.value].values,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            )
            data.hovertemplate = (
                f"<b>{'RA' if plotstate.geo_coords.value == 'celestial' else 'l'}</b>:"
                + " %{lon:.6f}<br>" +
                f"<b>{'DEC' if plotstate.geo_coords.value == 'celestial' else 'b'}</b>:"
                + " %{lat:.6f}<br>" + f"<b>{plotstate.color.value}</b>:" +
                " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                " %{customdata:.d}")

        def update_color():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # update main trace
            data = fig_widget.data[0]
            data.marker = dict(
                color=dff[plotstate.color.value].values,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            )
            data.hovertemplate = (
                f"<b>{'RA' if plotstate.geo_coords.value == 'celestial' else 'l'}</b>:"
                + " %{lon:.6f}<br>" +
                f"<b>{'DEC' if plotstate.geo_coords.value == 'celestial' else 'b'}</b>:"
                + " %{lat:.6f}<br>" + f"<b>{plotstate.color.value}</b>:" +
                " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                " %{customdata:.d}")

        def update_theme():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            fig_widget.update_layout(
                template=DARK_TEMPLATE if dark else LIGHT_TEMPLATE)
            fig_widget.update_geos(
                bgcolor="#212121" if dark else "#FAFAFA",
                lonaxis_gridcolor="#616161" if dark else "#BDBDBD",
                lataxis_gridcolor="#616161" if dark else "#BDBDBD",
            )

        sl.use_effect(update_data,
                      dependencies=[local_filter, plotstate.geo_coords.value])
        sl.use_effect(
            update_color,
            dependencies=[
                local_filter,
                plotstate.color.value,
                plotstate.colorscale.value,
            ],
        )
        sl.use_effect(update_theme, dependencies=[dark])
        sl.use_effect(
            set_flip,
            dependencies=[plotstate.flipx.value, plotstate.flipy.value])

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
            set_filter(df[df == dff[data["points"]["point_indexes"]]])

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


# PLOT SETTINGS


def show_settings(type, state):
    # plot controls
    if type == "scatter":
        return scatter_menu(state)
    elif type == "histogram":
        return statistics_menu(state)
    elif type == "aggregated":
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
                                       values=["celestial", "galactic"])
                sl.Select(
                    label="Projection",
                    value=plotstate.projection,
                    values=plotstate.Lookup["projections"],
                )
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
