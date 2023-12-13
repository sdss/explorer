import solara as sl
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
        marker=dict(
            color=c,
            colorbar=dict(title=PlotState.color.value),
            colorscale="viridis",
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

    return sl.FigurePlotly(fig)


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
    return sl.FigurePlotly(fig)


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
    if bintype == "count":
        y = dff.count(
            binby=[expr_x, expr_y],
            limits=[
                dff.minmax(PlotState.x.value),
                dff.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "mean":
        y = dff.mean(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                dff.minmax(PlotState.x.value),
                dff.minmax(PlotState.y.value)
            ],
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
    elif bintype == "mode":
        y = dff.mode(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                dff.minmax(PlotState.x.value),
                dff.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
        )
    elif bintype == "min":
        y = dff.min(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                dff.minmax(PlotState.x.value),
                dff.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "max":
        y = dff.max(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                dff.minmax(PlotState.x.value),
                dff.minmax(PlotState.y.value)
            ],
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
    return sl.FigurePlotly(fig)
