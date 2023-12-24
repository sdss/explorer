import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import solara as sl
import solara.lab as lab
from solara.express import CrossFilteredFigurePlotly  # noqa: this thing literally does not function with vaex frames

from state import State, PlotState
from util import check_catagorical


@sl.component
def show_plot(type):
    if State.df.value is not None:
        if PlotState.x.value is not None and PlotState.y.value is not None:
            if type == "histogram":
                histogram()
            elif type == "histogram2d":
                histogram2d()
            elif type == "scatter":
                # scatterplot()
                scatter()
        else:
            sl.ProgressLinear(True, color="purple")
    else:
        sl.Warning("Import or select a dataset to plot!")


@sl.component
def scatter3d():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-plot3d")

    dff = df
    if filter:
        dff = df[filter]
    selection = np.random.choice(int(len(dff)), PlotState.subset.value)
    x = np.array(dff[PlotState.x.value].values)[selection]
    y = np.array(dff[PlotState.y.value].values)[selection]
    z = np.array(dff[PlotState.color.value].values)[selection]

    fig = px.scatter_3d(
        x=x,
        y=y,
        z=z,
        log_x=PlotState.logx.value,
        log_y=PlotState.logy.value,
        labels={
            "x": PlotState.x.value,
            "y": PlotState.y.value,
            "z": PlotState.color.value,
        },
    )
    if PlotState.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if PlotState.flipy.value:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_title=PlotState.x.value,
                      yaxis_title=PlotState.y.value)
    return sl.FigurePlotly(fig)


@sl.component
def scatter():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-scatter")

    dff = df
    if filter:
        dff = df[filter]
    if len(dff) > 10000:
        x = dff[PlotState.x.value][:10_000]
        y = dff[PlotState.y.value][:10_000]
        c = dff[PlotState.color.value][:10_000]
    else:
        x = dff[PlotState.x.value]
        y = dff[PlotState.y.value]
        c = dff[PlotState.color.value]
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

    fig = go.Figure(data=go.Scattergl(
        x=x,
        y=y,
        mode="markers",
        hovertemplate=f"<b>{PlotState.x.value}</b>:" + " %{x:.6f}<br>" +
        f"<b>{PlotState.y.value}</b>:" + " %{y:.6f}<br>" +
        f"<b>{PlotState.color.value}</b>:" + " %{marker.color:.6f}",
        marker=dict(
            color=c,
            colorbar=dict(title=PlotState.color.value),
            colorscale=PlotState.colorscale.value,
        ),
    ), )
    if PlotState.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if PlotState.flipy.value:
        fig.update_yaxes(autorange="reversed")
    if PlotState.logx.value:
        fig.update_xaxes(type="log")
    if PlotState.logy.value:
        fig.update_yaxes(type="log")
    fig.update_layout(
        xaxis_title=PlotState.x.value,
        yaxis_title=PlotState.y.value,
        width=1000,
        height=1000,
    )

    def on_selection(data):
        set_filter((df[PlotState.x.value].isin(data["points"]["xs"])
                    & df[PlotState.y.value].isin(data["points"]["ys"])))

    def deselect(data):
        set_filter(None)

    return sl.FigurePlotly(
        fig,
        on_selection=on_selection,
        on_deselect=deselect,
        dependencies=[
            filter,
            PlotState.x.value,
            PlotState.y.value,
            PlotState.color.value,
            PlotState.colorscale.value,
            PlotState.logx.value,
            PlotState.logy.value,
            PlotState.flipx.value,
            PlotState.flipy.value,
        ],
    )


@sl.component
def histogram():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-histogram")

    dff = df
    if filter:
        dff = df[filter]
    expr = dff[PlotState.x.value]

    if check_catagorical(expr):
        x = expr.unique()
        y = []
        for i in x:
            # TODO: raise issue about vaex being unable to count catagorical data
            y.append(float(expr.str.count(i).sum()))
    else:
        x = dff.bin_centers(
            expression=expr,
            limits=dff.minmax(PlotState.x.value),
            shape=PlotState.nbins.value,
        )
        y = dff.count(
            binby=PlotState.x.value,
            limits=dff.minmax(PlotState.x.value),
            shape=PlotState.nbins.value,
        )
    if check_catagorical(expr):
        logx = False
    else:
        logx = PlotState.logx.value

    fig = px.histogram(
        x=x,
        y=y,
        nbins=PlotState.nbins.value,
        log_x=logx,
        log_y=PlotState.logy.value,
        histnorm=PlotState.norm.value,
        labels={
            "x": PlotState.x.value,
        },
    )
    fig.update_layout(
        xaxis_title=PlotState.x.value,
        yaxis_title="Frequency",
    )
    if PlotState.flipx.value:
        fig.update_xaxes(autorange="reversed")
    return sl.FigurePlotly(
        fig,
        dependencies=[
            filter,
            PlotState.nbins.value,
            PlotState.x.value,
            PlotState.logx.value,
            PlotState.logy.value,
            PlotState.flipx.value,
            PlotState.norm.value,
        ],
    )


@sl.component
def histogram2d():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-histogram2d")

    dff = df
    if filter:
        dff = df[filter]

    expr_x = dff[PlotState.x.value]
    expr_y = dff[PlotState.y.value]
    expr = dff[PlotState.color.value]
    x_cat = check_catagorical(expr_x)
    y_cat = check_catagorical(expr_y)
    if x_cat or y_cat:
        return sl.Warning(
            icon=True,
            label=
            "Selected columns are catagorical! Incompatible with histogram2d plot.",
        )

    bintype = str(PlotState.bintype.value)
    xlims = None
    ylims = None
    if xlims is None and ylims is None:
        limits = [dff.minmax(PlotState.x.value), dff.minmax(PlotState.y.value)]
    else:
        limits = [xlims, ylims]

    if bintype == "count":
        y = dff.count(
            binby=[expr_x, expr_y],
            limits=limits,
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "mean":
        y = dff.mean(
            expr,
            binby=[expr_x, expr_y],
            limits=limits,
            shape=PlotState.nbins.value,
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
        #        dff.minmax(PlotState.x.value),
        #        dff.minmax(PlotState.y.value)
        #    ],
        #    shape=PlotState.nbins.value,
        # )
    # elif bintype == "mode":
    #    y = dff.mode(
    #        expr,
    #        binby=[expr_x, expr_y],
    #        limits=[
    #            dff.minmax(PlotState.x.value),
    #            dff.minmax(PlotState.y.value)
    #        ],
    #        shape=PlotState.nbins.value,
    #    )
    elif bintype == "min":
        y = dff.min(
            expr,
            binby=[expr_x, expr_y],
            limits=limits,
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "max":
        y = dff.max(
            expr,
            binby=[expr_x, expr_y],
            limits=limits,
            shape=PlotState.nbins.value,
            array_type="xarray",
        )

    binscale = str(PlotState.binscale.value)
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

    if PlotState.flipy.value:
        origin = "upper"
    else:
        origin = "lower"

    fig = px.imshow(
        y.T,
        zmin=cmin,
        zmax=cmax,
        origin=origin,
        color_continuous_scale=PlotState.colorscale.value,
        labels={
            "x": PlotState.x.value,
            "y": PlotState.y.value,
            "color": PlotState.binscale.value,
        },
        width=1000,
        height=1000,
    )
    if PlotState.flipx.value:
        fig.update_xaxes(autorange="reversed")

    def select_bin(data):
        x_be = np.histogram_bin_edges(expr_x.evaluate(),
                                      bins=PlotState.nbins.value)
        xs = data["points"]["xs"][0]
        qx = np.abs(x_be - xs)
        px = np.sort(np.abs(x_be - xs))[0:2]
        ox = [qx == ps for ps in px]
        xi = np.logical_or(ox[0], ox[1])

        y_be = np.histogram_bin_edges(expr_y.evaluate(),
                                      bins=PlotState.nbins.value)
        ys = data["points"]["ys"][0]
        qy = np.abs(y_be - ys)
        py = np.sort(np.abs(y_be - ys))[0:2]
        oy = [qy == ps for ps in py]
        yi = np.logical_or(oy[0], oy[1])
        xlims = x_be[xi]
        ylims = y_be[yi]
        return

    def deselect_bin():
        xlims = None
        ylims = None
        return

    with sl.Column() as main:
        sl.FigurePlotly(
            fig,
            on_click=select_bin,
            dependencies=[
                filter,
                xlims,
                ylims,
                PlotState.nbins.value,
                PlotState.x.value,
                PlotState.y.value,
                PlotState.color.value,
                PlotState.colorscale.value,
                PlotState.logx.value,
                PlotState.logy.value,
                PlotState.flipx.value,
                PlotState.flipy.value,
                PlotState.binscale.value,
                PlotState.bintype.value,
            ],
        )
        sl.Button("Reset", on_click=deselect_bin())

    return
