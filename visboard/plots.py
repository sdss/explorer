import solara as sl
import numpy as np
import plotly.express as px

from state import State, PlotState


@sl.component
def show_plot(type):
    if State.df.value is not None:
        if PlotState.x.value is not None and PlotState.y.value is not None:
            if type == "histogram":
                histogramplot()
            elif type == "histogram2d":
                histogram2dplot()
            elif type == "scatter":
                scatterplot()
        else:
            sl.ProgressLinear(True, color="purple")
    else:
        sl.Warning("Import or select a dataset to plot!")


@sl.component
def scatterplot():
    dff = State.df.value
    dff.select(dff[PlotState.x.value], PlotState.x.value != None)
    x = dff.evaluate(dff[PlotState.x.value], selection=True)
    y = dff.evaluate(dff[PlotState.y.value], selection=True)
    c = dff.evaluate(dff[PlotState.color.value], selection=True)

    fig = px.scatter(
        x=x,
        y=y,
        color=c,
        log_x=PlotState.logx.value,
        log_y=PlotState.logy.value,
        width=1600,
        height=1000,
    )
    if PlotState.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if PlotState.flipy.value:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_title=PlotState.x.value,
                      yaxis_title=PlotState.y.value)
    return sl.FigurePlotly(fig)


@sl.component
def histogramplot():
    df = State.df.value
    expr = df[PlotState.x.value]
    x = df.bin_centers(
        expression=expr,
        limits=df.minmax(PlotState.x.value),
        shape=PlotState.nbins.value,
    )
    counts = df.count(
        binby=PlotState.x.value,
        limits=df.minmax(PlotState.x.value),
        shape=PlotState.nbins.value,
    )
    fig = px.histogram(
        x=x,
        y=counts,
        nbins=PlotState.nbins.value,
        log_y=PlotState.logy.value,
        histnorm=PlotState.norm.value,
    )
    fig.update_layout(xaxis_title=PlotState.x.value, yaxis_title="Frequency")
    return sl.FigurePlotly(fig)


@sl.component
def histogram2dplot():
    df = State.df.value
    expr_x = df[PlotState.x.value]
    expr_y = df[PlotState.y.value]
    counts = df.count(
        binby=[expr_x, expr_y],
        limits=[df.minmax(PlotState.x.value),
                df.minmax(PlotState.y.value)],
        shape=PlotState.nbins.value,
        array_type="xarray",
    )
    fig = px.imshow(
        np.log1p(counts).T,
        labels={
            "x": PlotState.x.value,
            "y": PlotState.y.value,
            "color": "Counts"
        },
    )
    return sl.FigurePlotly(fig)
