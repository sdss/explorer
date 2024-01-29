import operator
import webbrowser as wb

from functools import reduce
from time import perf_counter as timer

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import reacton.ipyvuetify as rv
import solara as sl
from plotly.graph_objs._figurewidget import FigureWidget
from solara.lab import Menu, ContextMenu

from state import State
from plot_settings import show_settings
from util import check_catagorical

DARK_TEMPLATE = dict(layout=go.Layout(
    font=dict(color="white", size=16),
    showlegend=False,
    paper_bgcolor="#424242",
    autosize=True,
    plot_bgcolor="#212121",
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
        self.nbins = sl.use_reactive(200)
        self.bintype = sl.use_reactive("mean")
        self.binscale = sl.use_reactive(None)
        self.norm = sl.use_reactive(None)

        # skyplot settings
        self.geo_coords = sl.use_reactive("ra/dec")
        self.projection = sl.use_reactive("hammer")

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
    return


def update_relayout(fig, relayout, plotstate):
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


def show_plot(type, del_func):
    with rv.Card(class_="grey darken-3", style_="width: 100%; height: 100%"):
        plotstate = PlotState()
        with rv.CardText():
            with sl.Column(classes=["grey darken-3"]):
                if type == "histogram":
                    histogram(plotstate)
                elif type == "histogram2d":
                    histogram2d(plotstate)
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
def scatter3d(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-plot3d")

    dff = df
    if filter:
        dff = df[filter]
    selection = np.random.choice(int(len(dff)), plotstate.subset.value)
    x = np.array(dff[plotstate.x.value].values)[selection]
    y = np.array(dff[plotstate.y.value].values)[selection]
    z = np.array(dff[plotstate.color.value].values)[selection]

    fig = px.scatter_3d(
        x=x,
        y=y,
        z=z,
        log_x=plotstate.logx.value,
        log_y=plotstate.logy.value,
        labels={
            "x": plotstate.x.value,
            "y": plotstate.y.value,
            "z": plotstate.color.value,
        },
    )
    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if plotstate.flipy.value:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title=plotstate.x.value,
        autosize=True,
        yaxis_title=plotstate.y.value,
    )
    return sl.FigurePlotly(fig)


@sl.component
def scatter(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-scatter")
    relayout, set_relayout = sl.use_state(None)
    xfilter, set_xfilter = sl.use_state(None)
    yfilter, set_yfilter = sl.use_state(None)
    hovered, set_hovered = sl.use_state(False)
    clicked, set_clicked = sl.use_state(False)
    sdssid, set_sdssid = sl.use_state(None)

    # filter
    if filter:
        dff = df[filter]
    else:
        dff = df

    # get minmax for reset
    xmm = dff.minmax(plotstate.x.value)
    ymm = dff.minmax(plotstate.y.value)

    # filter to current relayout
    if plotstate.reactive.value == "on":
        # TODO: this logic sequence is cursed and high complexity fix it
        if relayout is not None:
            if "xaxis.autorange" in relayout.keys():
                set_xfilter(None)
                set_yfilter(None)
            if "xaxis.range[0]" in relayout.keys():
                min = relayout["xaxis.range[0]"]
                max = relayout["xaxis.range[1]"]
                set_xfilter(df[
                    f"(({plotstate.x.value} > {np.min((min,max))}) & ({plotstate.x.value} < {np.max((min,max))}))"]
                            )
            if "yaxis.range[0]" in relayout.keys():
                min = relayout["yaxis.range[0]"]
                max = relayout["yaxis.range[1]"]
                set_yfilter(df[
                    f"(({plotstate.y.value} > {np.min((min,max))}) & ({plotstate.y.value} < {np.max((min,max))}))"]
                            )
            local_filters = [xfilter, yfilter]
            if local_filters[0] is not None and local_filters[1] is not None:
                if filter:
                    superfilter = reduce(operator.and_, local_filters, filter)
                    dff = df[superfilter]
                else:
                    superfilter = reduce(operator.and_, local_filters[1:],
                                         local_filters[0])
                    dff = df[superfilter]
            else:
                if filter:
                    dff = df[filter]
                else:
                    dff = df
        else:
            if filter:
                dff = df[filter]
            else:
                dff = df
    else:
        if filter:
            dff = df[filter]
        else:
            dff = df

    # get cols
    x = dff[plotstate.x.value]
    y = dff[plotstate.y.value]
    c = dff[plotstate.color.value]
    ids = dff["sdss_id"]

    # trim to renderable length
    if len(dff) > 20000:
        x = x[:20_000]
        y = y[:20_000]
        c = c[:20_000]
        ids = ids[:20_000]

    # Check for catagorical (unrenderable in scatter)
    x_cat = check_catagorical(x)
    y_cat = check_catagorical(y)
    if x_cat or y_cat:
        return sl.Warning(
            icon=True,
            label=
            "Selected columns are catagorical! Incompatible with scatter plot.",
        )
    x = x.values
    y = y.values
    c = c.values
    ids = ids.values

    fig = go.Figure(
        data=go.Scattergl(
            x=x,
            y=y,
            mode="markers",
            customdata=ids,
            hovertemplate=f"<b>{plotstate.x.value}</b>:" + " %{x:.6f}<br>" +
            f"<b>{plotstate.y.value}</b>:" + " %{y:.6f}<br>" +
            f"<b>{plotstate.color.value}</b>:" + " %{marker.color:.6f}<br>" +
            "<b>ID</b>:" + " %{customdata:.d}",
            marker=dict(
                color=c,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            ),
        ),
        layout=go.Layout(
            xaxis_title=plotstate.x.value,
            yaxis_title=plotstate.y.value,
            template=DARK_TEMPLATE,
        ),
    )
    # flip and log
    if plotstate.flipx.value:
        # TODO: fix the flip on dynamic render (cant use autorange have to used manual logic aijijhitjhij)
        fig.update_xaxes(range=fig.layout.xaxes.range.reverse())
    if plotstate.flipy.value:
        fig.update_yaxes(autorange="reversed")
    if plotstate.logx.value:
        fig.update_xaxes(type="log")
    if plotstate.logy.value:
        fig.update_yaxes(type="log")

    # change autorange min-max to allow for a reset to max range
    # TODO: need to add fix for reversed
    fig.update_xaxes(autorangeoptions_minallowed=xmm[0],
                     autorangeoptions_maxallowed=xmm[1])
    fig.update_yaxes(autorangeoptions_minallowed=ymm[0],
                     autorangeoptions_maxallowed=ymm[1])
    """Relayout handlers"""
    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout, plotstate)

    def reset_lims():
        set_relayout(None)
        set_xfilter(None)
        set_yfilter(None)

    sl.use_thread(
        reset_lims,
        dependencies=[
            plotstate.x.value,
            plotstate.y.value,
            plotstate.logx.value,
            plotstate.logy.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )

    def relayout_callback(data):
        if data is not None:
            set_relayout(data["relayout_data"])

    """Selection handlers"""

    def on_selection(data):
        print(len(data["points"]["xs"]))
        if len(data["points"]["xs"]) > 0:
            set_filter((df[plotstate.x.value].isin(data["points"]["xs"])
                        & df[plotstate.y.value].isin(data["points"]["ys"])))

    def on_deselect(data):
        set_filter(None)

    """
    Context Menu handlers
    """

    def on_click(data):
        set_clicked(True)

    def on_hover(data):
        set_clicked(False)
        set_hovered(True)
        set_sdssid(df[plotstate.x.value].isin(data["points"]["xs"])
                   & df[plotstate.y.value].isin(data["points"]["ys"]))

    def on_unhover(data):
        if not clicked:
            set_hovered(False)

    def open_jdaviz():
        wb.open("http://localhost:8866/")
        close_context_menu()

    def download_spectra():
        # TODO: change to directly use ID
        if sdssid is not None:
            print(df[sdssid]["sdss_id"].values[0])
        else:
            raise ValueError("SDSS ID was none on scatter hover.")
        wb.open("https://www.google.com")
        close_context_menu()

    def close_context_menu():
        set_hovered(False)
        set_clicked(False)

    fig = sl.FigurePlotly(
        fig,
        on_hover=on_hover,
        on_click=on_click,
        on_unhover=on_unhover,
        on_selection=on_selection,
        on_deselect=on_deselect,
        on_relayout=relayout_callback,
        dependencies=[
            filter,
            xfilter,
            yfilter,
            plotstate.x.value,
            plotstate.y.value,
            plotstate.color.value,
            plotstate.colorscale.value,
            plotstate.logx.value,
            plotstate.logy.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )
    with ContextMenu(activator=fig):
        if clicked & hovered:
            sl.Column(
                gap="0px",
                children=[
                    sl.Button(
                        label="Download spectra",
                        icon_name="mdi-file-chart-outline",
                        on_click=download_spectra,
                        small=True,
                    ),
                    sl.Button(
                        label="Open in Jdaviz",
                        icon_name="mdi-chart-line",
                        on_click=open_jdaviz,
                        small=True,
                    ),
                ],
            )

    return


@sl.component
def histogram(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-histogram")
    relayout, set_relayout = sl.use_state(None)

    dff = df
    if filter:
        dff = df[filter]
    expr = dff[plotstate.x.value]

    def perform_binning():
        tstart = timer()
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
        print(timer() - tstart)
        return x, y

    x, y = sl.use_memo(
        perform_binning,
        dependencies=[filter, plotstate.x.value, plotstate.nbins.value],
    )

    if check_catagorical(expr):
        logx = False
    else:
        logx = plotstate.logx.value

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
        template=DARK_TEMPLATE,
    )
    fig.update_yaxes(title="Frequency")
    fig.update_layout(margin_r=10)

    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")

    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout, plotstate)

    def reset_lims():
        set_relayout(None)

    sl.use_thread(
        reset_lims,
        dependencies=[
            plotstate.x.value,
            plotstate.logx.value,
            plotstate.logy.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )

    def on_selection(data):
        print(data)
        filters = list()
        if len(data["points"]["xs"]) > 0:
            for cent in np.unique(data["points"]["xs"]):
                filters.append(
                    df[f"({plotstate.x.value} <= {cent + binsize})"]
                    & df[f"({plotstate.x.value} >= {cent - binsize})"])
            filters = reduce(operator.or_, filters[1:], filters[0])
            set_filter(filters)

    def on_deselect(data):
        set_filter(None)

    def relayout_callback(data):
        if data is not None:
            set_relayout(data["relayout_data"])

    fig_el = sl.FigurePlotly(
        fig,
        on_selection=on_selection,
        on_deselect=on_deselect,
        on_relayout=relayout_callback,
        dependencies=[
            filter,
            plotstate.nbins.value,
            plotstate.x.value,
            plotstate.logx.value,
            plotstate.logy.value,
            plotstate.flipx.value,
            plotstate.norm.value,
        ],
    )

    return fig_el


@sl.component
def histogram2d(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-histogram2d")
    relayout, set_relayout = sl.use_state(None)

    dff = df
    if filter:
        dff = df[filter]

    def perform_binning():
        expr = (dff[plotstate.x.value], dff[plotstate.y.value])
        expr_c = dff[plotstate.color.value]
        x_cat = check_catagorical(expr[0])
        y_cat = check_catagorical(expr[1])
        if x_cat or y_cat:
            return sl.Warning(
                icon=True,
                label=
                "Selected columns are catagorical! Incompatible with histogram2d plot.",
            )
        bintype = str(plotstate.bintype.value)

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
            return sl.Warning(
                label="Median has memory issues. Remains unimplemented.",
                icon=True)
            # WARNING: do not use median_approx -- it consumed 9T of memory.
            # y = dff.median_approx(
            #    expr,
            #    binby=[expr_x, expr_y],
            #    limits=[
            #        dff.minmax(plotstate.x.value),
            #        dff.minmax(plotstate.y.value)
            #    ],
            #    shape=plotstate.nbins.value,
            # )
        # elif bintype == "mode":
        #    y = dff.mode(
        #        expr,
        #        binby=[expr_x, expr_y],
        #        limits=[
        #            dff.minmax(plotstate.x.value),
        #            dff.minmax(plotstate.y.value)
        #        ],
        #        shape=plotstate.nbins.value,
        #    )
        elif bintype == "min":
            y = dff.min(
                expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
            )
        elif bintype == "max":
            y = dff.max(
                expr_c,
                binby=expr,
                limits=limits,
                shape=plotstate.nbins.value,
                array_type="xarray",
            )

        binscale = str(plotstate.binscale.value)
        if binscale == "log1p":
            y = np.log1p(y)
        elif binscale == "log10":
            y = np.log10(y)

        # TODO: clean this code
        y = y.where(y != np.inf, np.nan)
        y = y.where(y != -np.inf, np.nan)
        cmin = float(np.min(y).values)
        cmax = float(np.max(y).values)
        y = y.fillna(-999)
        return y, cmin, cmax

    z, cmin, cmax = sl.use_memo(
        perform_binning,
        dependencies=[
            filter,
            plotstate.x.value,
            plotstate.y.value,
            plotstate.bintype.value,
            plotstate.nbins.value,
            plotstate.binscale.value,
        ],
    )

    if plotstate.flipy.value:
        origin = "upper"
    else:
        origin = "lower"

    fig = px.imshow(
        z.T,
        zmin=cmin,
        zmax=cmax,
        origin=origin,
        color_continuous_scale=plotstate.colorscale.value,
        labels={
            "x": plotstate.x.value,
            "y": plotstate.y.value,
            "color": plotstate.color.value + f"({plotstate.bintype.value})",
        },
        template=DARK_TEMPLATE,
    )
    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")

    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout, plotstate)

    def reset_lims():
        set_relayout(None)

    sl.use_thread(
        reset_lims,
        dependencies=[
            plotstate.x.value,
            plotstate.y.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )

    def relayout_callback(data):
        if data is not None:
            set_relayout(data["relayout_data"])

    def select_bin(data):
        return
        x_be = np.histogram_bin_edges(expr_x.evaluate(),
                                      bins=plotstate.nbins.value)
        xs = data["points"]["xs"][0]
        qx = np.abs(x_be - xs)
        px = np.sort(np.abs(x_be - xs))[0:2]
        ox = [qx == ps for ps in px]
        xi = np.logical_or(ox[0], ox[1])

        y_be = np.histogram_bin_edges(expr_y.evaluate(),
                                      bins=plotstate.nbins.value)
        ys = data["points"]["ys"][0]
        qy = np.abs(y_be - ys)
        py = np.sort(np.abs(y_be - ys))[0:2]
        oy = [qy == ps for ps in py]
        yi = np.logical_or(oy[0], oy[1])
        set_xlims(x_be[xi])
        set_ylims(y_be[yi])
        return

    def deselect_bin():
        return
        set_xlims(None)
        set_ylims(None)
        return

    fig.update_layout(font=dict(size=16), autosize=True)

    with sl.Column() as main:
        sl.FigurePlotly(
            fig,
            on_click=select_bin,
            on_relayout=relayout_callback,
            dependencies=[
                filter,
                # xlims,
                # ylims,
                plotstate.nbins.value,
                plotstate.y.value,
                plotstate.color.value,
                plotstate.colorscale.value,
                plotstate.logx.value,
                plotstate.logy.value,
                plotstate.flipx.value,
                plotstate.flipy.value,
                plotstate.binscale.value,
                plotstate.bintype.value,
            ],
        )
        # sl.Button("Reset", on_click=deselect_bin)

    return main


@sl.component
def skyplot(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "scattergeo")
    sdssid, set_sdssid = sl.use_state(None)
    rerange, set_rerange = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)

    if filter is not None:
        dff = df[filter]
    else:
        dff = df

    def remake_filters():
        print("skyplot: remake filters")
        tstart = timer()
        if plotstate.geo_coords.value == "ra/dec":
            lon = "ra"
            lat = "dec"
        else:
            lon = "l"
            lat = "b"
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
            (0 + ((-180 / scale + lon_center) % 360) + 360) % 360,
            (0 + ((180 / scale + lon_center) % 360) + 360) % 360,
        )
        latlow, lathigh = (
            np.max((lat_center - (90 / scale), -90)),
            np.min((lat_center + (90 / scale), 90)),
        )

        # create and set filter objects
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
        print(f"Time: {timer() - tstart}")

    sl.use_memo(remake_filters, dependencies=[rerange])

    if local_filter is not None:
        dff = dff[local_filter]
    dff = dff[:1_000]

    # get correct col based on coords setting
    dtick = 30  # for tickers
    if plotstate.geo_coords.value == "ra/dec":
        lon = dff["ra"]
        lat = dff["dec"]
        lon_label = "RA"
        lat_label = "DEC"
        x = list(range(-180, 180 + dtick, dtick))
    else:
        lon = dff["l"]
        lat = dff["b"]
        lon_label = "l"
        lat_label = "b"
        x = list(range(0, 360 + dtick, dtick))
    y = list(range(-90, 90 + dtick, dtick))

    c = dff[plotstate.color.value]
    ids = dff["sdss_id"]

    print("skyplot: rerendering fig start")
    tstart = timer()
    fig = go.Figure(
        data=go.Scattergeo(
            lat=lat.values,
            lon=lon.values,
            mode="markers",
            customdata=ids.values,
            hovertemplate=f"<b>{lon_label}</b>:" + " %{lon:.6f}<br>" +
            f"<b>{lat_label}</b>:" + " %{lat:.6f}<br>" +
            f"<b>{plotstate.color.value}</b>:" + " %{marker.color:.6f}<br>" +
            "<b>ID</b>:" + " %{customdata:.d}",
            marker=dict(
                color=c.values,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            ),
        ),
        layout=go.Layout(template=DARK_TEMPLATE),
    )

    xpos = 0
    ypos = 0
    fig.add_trace(
        go.Scattergeo({
            "lon": x[1:-1] + [xpos] * (len(y) - 2),
            "lat": [ypos] * (len(x) - 2) + y[1:-1],
            "showlegend": False,
            "text": x[1:-1] + y[1:-1],
            "mode": "text",
        }))
    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if plotstate.flipy.value:
        fig.update_yaxes(autorange="reversed")
    fig.update_geos(
        projection_type=plotstate.projection.value,
        bgcolor="#212121",
        visible=False,
        lonaxis_showgrid=True,
        lonaxis_tick0=0,
        lonaxis_gridcolor="#616161",
        lataxis_showgrid=True,
        lataxis_tick0=0,
        lataxis_gridcolor="#616161",
    )
    fig.update_layout(margin={"t": 30, "b": 10, "l": 0, "r": 0})

    # reset the ranges based on the relayout
    fig = update_relayout(fig, rerange, plotstate)

    def reset_lims():
        set_rerange({})

    print(f"Time: {timer() - tstart}")

    sl.use_thread(
        reset_lims,
        dependencies=[
            plotstate.geo_coords.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )

    def relayout_callback(data):
        print("skyplot: relayout called")
        start = timer()
        if data is not None:
            if "geo.fitbounds" in data["relayout_data"].keys():
                set_rerange({})
                set_local_filter(None)
            else:
                if data["relayout_data"] is not None:
                    set_rerange(dict(rerange, **data["relayout_data"]))
        print(f"Time relayout: {timer() - start}")

    """Selection handlers"""

    def on_select(data):
        if len(data["points"]["xs"]) > 0:
            set_filter(df[df == dff[data["points"]["point_indexes"]]])

    def on_deselect(data):
        set_filter(None)

    """
    Context Menu handlers
    """

    def open_jdaviz():
        wb.open("http://localhost:8866/")
        close_context_menu()

    def download_spectra():
        # TODO: change to directly use ID
        print(sdssid[0])
        wb.open("https://www.google.com")
        close_context_menu()

    def close_context_menu():
        set_hovered(False)

    fig = sl.FigurePlotly(
        fig,
        on_click=print,
        on_selection=on_select,
        on_deselect=on_deselect,
        on_relayout=relayout_callback,
        dependencies=[
            filter,
            local_filter,
            plotstate.geo_coords.value,
            plotstate.projection.value,
            plotstate.color.value,
            plotstate.colorscale.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )
    # with ContextMenu(activator=fig,
    #                 open_value=menu_open,
    #                 on_open_value=set_menu_open):
    #    if hovered & menu_open:
    #        sl.Column(
    #            gap="0px",
    #            children=[
    #                sl.Button(
    #                    label="Download spectra",
    #                    icon_name="mdi-file-chart-outline",
    #                    on_click=download_spectra,
    #                    small=True,
    #                ),
    #                sl.Button(
    #                    label="Open in Jdaviz",
    #                    icon_name="mdi-chart-line",
    #                    on_click=open_jdaviz,
    #                    small=True,
    #                ),
    #            ],
    #        )
    return
