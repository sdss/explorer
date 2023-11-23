import solara as sl
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from solara.express import CrossFilteredFigurePlotly

from state import State, PlotState


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
            elif type == "3d":
                scatter3d()
        else:
            sl.ProgressLinear(True, color="purple")
    else:
        sl.Warning("Import or select a dataset to plot!")


@sl.component
def scatter3d():
    dff = State.df.value
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
    dff = State.df.value
    selection = np.random.choice(int(len(dff)), PlotState.subset.value)
    x = np.array(dff[PlotState.x.value].values)[selection]
    y = np.array(dff[PlotState.y.value].values)[selection]
    c = np.array(dff[PlotState.color.value].values)[selection]
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
    expr = df[PlotState.x.value]
    x = df.bin_centers(
        expression=expr,
        limits=df.minmax(PlotState.x.value),
        shape=PlotState.nbins.value,
    )
    y = df.count(
        binby=PlotState.x.value,
        limits=df.minmax(PlotState.x.value),
        shape=PlotState.nbins.value,
    )

    fig = px.histogram(
        x=x,
        y=y,
        nbins=PlotState.nbins.value,
        log_x=PlotState.logx.value,
        log_y=PlotState.logy.value,
        histnorm=PlotState.norm.value,
        labels={
            "x": PlotState.x.value,
        },
    )
    fig.update_layout(xaxis_title=PlotState.x.value, yaxis_title="Frequency")
    return sl.FigurePlotly(fig)


@sl.component
def histogram2d():
    df = State.df.value
    expr_x = df[PlotState.x.value]
    expr_y = df[PlotState.y.value]
    expr = PlotState.color.value

    bintype = str(PlotState.bintype.value)
    if bintype == "count":
        y = df.count(
            binby=[expr_x, expr_y],
            limits=[
                df.minmax(PlotState.x.value),
                df.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "mean":
        y = df.mean(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                df.minmax(PlotState.x.value),
                df.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "median":
        sl.Warning(label="Median has memory issues. Remains unimplemented.",
                   icon=True)
        # WARNING: do not use median_approx -- it consumed 9T of memory.
        # y = df.median_approx(
        #    expr,
        #    binby=[expr_x, expr_y],
        #    limits=[
        #        df.minmax(PlotState.x.value),
        #        df.minmax(PlotState.y.value)
        #    ],
        #    shape=PlotState.nbins.value,
        # )
    elif bintype == "mode":
        y = df.mode(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                df.minmax(PlotState.x.value),
                df.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
        )
    elif bintype == "min":
        y = df.min(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                df.minmax(PlotState.x.value),
                df.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
            array_type="xarray",
        )
    elif bintype == "max":
        y = df.max(
            expr,
            binby=[expr_x, expr_y],
            limits=[
                df.minmax(PlotState.x.value),
                df.minmax(PlotState.y.value)
            ],
            shape=PlotState.nbins.value,
            array_type="xarray",
        )

    binscale = str(PlotState.binscale.value)
    if binscale == "log1p":
        y = np.log1p(y)
    elif binscale == "log10":
        y = np.log10(y)

    print(y)
    fig = px.imshow(
        y.T,
        labels={
            "x": PlotState.x.value,
            "y": PlotState.y.value,
            "color": PlotState.binscale.value,
        },
    )
    return sl.FigurePlotly(fig)
