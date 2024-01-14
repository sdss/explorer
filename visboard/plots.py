import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import reacton.ipyvuetify as rv

import solara as sl
from solara.express import CrossFilteredFigurePlotly  # noqa: this thing literally does not function with vaex frames

from state import State
from util import check_catagorical


def update_relayout(fig, relayout):
    if relayout is not None:
        if "xaxis.range[0]" in relayout.keys():
            fig.update_xaxes(
                range=[relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]])
        if "yaxis.range[0]" in relayout.keys():
            fig.update_yaxes(
                range=[relayout["yaxis.range[0]"], relayout["yaxis.range[1]"]])

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


@sl.component
def show_plot(type, plotstate):
    # failsafe conditional checks
    if State.df.value is not None:
        if plotstate.x.value is not None and plotstate.y.value is not None:
            if type == "histogram":
                histogram(plotstate)
            elif type == "histogram2d":
                histogram2d(plotstate)
            elif type == "scatter":
                # scatterplot()
                scatter(plotstate)
            elif type == "skyplot":
                skyplot(plotstate)
        else:
            sl.ProgressLinear(True, color="purple")
    else:
        sl.Warning("Import or select a dataset to plot!")


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

    dff = df
    if filter:
        dff = df[filter]

    # get cols
    x = dff[plotstate.x.value]
    y = dff[plotstate.y.value]
    c = dff[plotstate.color.value]
    ids = dff["sdss_id"]

    # trim to renderable length
    if len(dff) > 10000:
        x = x[:10_000]
        y = y[:10_000]
        c = c[:10_000]
        ids = ids[:10_000]

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

    fig = go.Figure(data=go.Scattergl(
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
    ), )
    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if plotstate.flipy.value:
        fig.update_yaxes(autorange="reversed")
    if plotstate.logx.value:
        fig.update_xaxes(type="log")
    if plotstate.logy.value:
        fig.update_yaxes(type="log")
    fig.update_layout(
        xaxis_title=plotstate.x.value,
        yaxis_title=plotstate.y.value,
        autosize=True,
        height=700,
    )
    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout)

    def reset_lims():
        set_relayout(None)

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

    def on_selection(data):
        set_filter((df[plotstate.x.value].isin(data["points"]["xs"])
                    & df[plotstate.y.value].isin(data["points"]["ys"])))

    def deselect(data):
        set_filter(None)

    return sl.FigurePlotly(
        fig,
        on_selection=on_selection,
        on_deselect=deselect,
        on_relayout=relayout_callback,
        dependencies=[
            filter,
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


@sl.component
def histogram(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-histogram")
    relayout, set_relayout = sl.use_state(None)

    dff = df
    if filter:
        dff = df[filter]
    expr = dff[plotstate.x.value]

    if check_catagorical(expr):
        x = expr.unique()
        y = []
        for i in x:
            # TODO: raise issue about vaex being unable to count catagorical data
            y.append(float(expr.str.count(i).sum()))
    else:
        # make x (bin centers) and y (counts)
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
    )
    fig.update_layout(
        xaxis_title=plotstate.x.value,
        yaxis_title="Frequency",
        font=dict(size=16),
        autosize=True,
    )

    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")

    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout)

    def reset_lims():
        set_relayout(None)

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

    fig_el = sl.FigurePlotly(
        fig,
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

    expr_x = dff[plotstate.x.value]
    expr_y = dff[plotstate.y.value]
    expr = dff[plotstate.color.value]
    x_cat = check_catagorical(expr_x)
    y_cat = check_catagorical(expr_y)
    if x_cat or y_cat:
        return sl.Warning(
            icon=True,
            label=
            "Selected columns are catagorical! Incompatible with histogram2d plot.",
        )
    bintype = str(plotstate.bintype.value)

    xlims, set_xlims = sl.use_state(None)
    ylims, set_ylims = sl.use_state(None)
    if xlims is None and ylims is None:
        limits = [dff.minmax(plotstate.x.value), dff.minmax(plotstate.y.value)]
    else:
        limits = [xlims, ylims]

    if bintype == "count":
        y = dff.count(
            binby=[expr_x, expr_y],
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
        )
    elif bintype == "mean":
        y = dff.mean(
            expr,
            binby=[expr_x, expr_y],
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
            expr,
            binby=[expr_x, expr_y],
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
        )
    elif bintype == "max":
        y = dff.max(
            expr,
            binby=[expr_x, expr_y],
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

    if plotstate.flipy.value:
        origin = "upper"
    else:
        origin = "lower"

    fig = px.imshow(
        y.T,
        zmin=cmin,
        zmax=cmax,
        origin=origin,
        color_continuous_scale=plotstate.colorscale.value,
        labels={
            "x": plotstate.x.value,
            "y": plotstate.y.value,
            "color": plotstate.binscale.value,
        },
    )
    if plotstate.flipx.value:
        fig.update_xaxes(autorange="reversed")

    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout)

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
                xlims,
                ylims,
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
        sl.Button("Reset", on_click=deselect_bin)

    return main


@sl.component
def skyplot(plotstate):
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "scattergeo")
    relayout, set_relayout = sl.use_state(None)

    dff = df
    if filter:
        dff = dff[filter]
    dff = dff[:10_000]

    if plotstate.geo_coords.value == "ra/dec":
        lon = dff["ra"]
        lat = dff["dec"]
        lon_label = "RA"
        lat_label = "DEC"
        print("sky:radec")
        projection = "aitoff"
    else:
        lon = dff["l"]
        lat = dff["b"]
        lon_label = "l"
        lat_label = "b"
        print("sky:galcoords")
        projection = "mollweide"
    c = dff[plotstate.color.value]
    ids = dff["sdss_id"]
    fig = go.Figure(data=go.Scattergeo(
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
    ), )
    # add "label" trace
    dtick = 30
    x = list(range(-180, 180 + dtick, dtick))
    y = list(range(-90, 90 + dtick, dtick))
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
    fig.update_layout(autosize=True, height=700)
    fig.update_geos(
        projection_type=projection,
        bgcolor="#ccc",
        visible=False,
        lonaxis_showgrid=True,
        lonaxis_dtick=5,
        lonaxis_tick0=0,
        lataxis_showgrid=True,
        lataxis_dtick=5,
        lataxis_tick0=0,
    )
    fig.update_layout(margin={"t": 30, "b": 10, "l": 0, "r": 0})

    # reset the ranges based on the relayout
    fig = update_relayout(fig, relayout)

    def reset_lims():
        set_relayout(None)

    sl.use_thread(
        reset_lims,
        dependencies=[
            plotstate.geo_coords.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )

    def relayout_callback(data):
        if data is not None:
            print(data)
            set_relayout(data["relayout_data"])

    return sl.FigurePlotly(
        fig,
        on_relayout=relayout_callback,
        dependencies=[
            filter,
            plotstate.geo_coords.value,
            plotstate.color.value,
            plotstate.colorscale.value,
            plotstate.flipx.value,
            plotstate.flipy.value,
        ],
    )
