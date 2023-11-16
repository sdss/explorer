from re import S
from typing import Optional, cast

import pandas as pd
import vaex as vx
import plotly.express as px
import numpy as np

import solara
import solara.express as solara_px  # similar to plotly express, but comes with cross filters
import solara.lab
from solara.components.columns import Columns
from solara.components.file_drop import FileDrop

github_url = solara.util.github_url(__file__)
try:
    # fails on pyodide
    # df_sample = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv")
    # df_sample = pd.read_parquet(
    # "/home/riley/uni/rproj/data/allApogeeNetStar-0.4.0.parquet").dropna()
    # df_sample = vx.example()
    df_sample = vx.open(
        "/home/riley/uni/rproj/data/allApogeeNetStar-0.4.0.parquet")
except:  # noqa
    df_sample = None


class State:
    plottype = solara.reactive("scatter")
    size_max = solara.reactive(40.0)
    size = solara.reactive(cast(Optional[str], None))
    color = solara.reactive(cast(Optional[str], None))
    x = solara.reactive(cast(Optional[str], None))
    y = solara.reactive(cast(Optional[str], None))
    logx = solara.reactive(False)
    logy = solara.reactive(False)
    flipx = solara.reactive(False)
    flipy = solara.reactive(False)
    nbins = solara.reactive(cast(Optional[int], None))
    df = solara.reactive(cast(Optional[vx.DataFrame], None))
    norms = [None, "percent", "probability", "density", "probability density"]
    norm = solara.reactive(cast(Optional[str], None))

    @staticmethod
    def load_sample():
        State.x.value = str("TEFF")
        State.y.value = str("LOGG")
        State.size.value = str("E_TEFF")
        State.color.value = str("FE_H")
        State.nbins.value = 100
        State.df.value = df_sample

    @staticmethod
    def load_from_file(file):
        df = vx.open(file["file_obj"])
        State.x.value = str(df.columns[0])
        State.y.value = str(df.columns[1])
        State.size.value = str(df.columns[2])
        State.color.value = str(df.columns[3])
        State.nbins.value = 100
        State.df.value = df

    @staticmethod
    def reset():
        State.df.value = None


@solara.component
def scatterplot():
    df = State.df.value
    fig = px.scatter(
        x=df[State.x.value].values,
        y=df[State.y.value].values,
        size=df[State.size.value].values,
        color=df[State.color.value].values,
        size_max=State.size_max.value,
        log_x=State.logx.value,
        log_y=State.logy.value,
    )
    if State.flipx.value:
        fig.update_xaxes(autorange="reversed")
    if State.flipy.value:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_title=State.x.value, yaxis_title=State.y.value)
    return solara.FigurePlotly(fig)


@solara.component
def histogramplot():
    df = State.df.value
    expr = df[State.x.value]
    x = df.bin_centers(
        expression=expr,
        limits=df.minmax(State.x.value),
        shape=State.nbins.value,
    )
    counts = df.count(
        binby=State.x.value,
        limits=df.minmax(State.x.value),
        shape=State.nbins.value,
    )
    fig = px.histogram(
        x=x,
        y=counts,
        nbins=State.nbins.value,
        log_y=State.logy.value,
        histnorm=State.norm.value,
    )
    fig.update_layout(xaxis_title=State.x.value, yaxis_title="Frequency")
    return solara.FigurePlotly(fig)


@solara.component
def histogram2dplot():
    df = State.df.value
    expr_x = df[State.x.value]
    expr_y = df[State.y.value]
    counts = df.count(
        binby=[expr_x, expr_y],
        limits=[df.minmax(State.x.value),
                df.minmax(State.y.value)],
        shape=State.nbins.value,
        array_type="xarray",
    )
    fig = px.imshow(np.log1p(counts).T)
    fig.update_layout(xaxis_title=State.x.value, yaxis_title=State.y.value)
    return solara.FigurePlotly(fig)


@solara.component
def Page():
    df = State.df.value

    with solara.Sidebar():
        with solara.Card("Controls", margin=0, elevation=0):
            with solara.Column():
                with solara.Row():
                    solara.Button(
                        "Sample dataset",
                        color="primary",
                        text=True,
                        outlined=True,
                        on_click=State.load_sample,
                        disabled=df is not None,
                    )
                    solara.Button(
                        "Clear dataset",
                        color="primary",
                        text=True,
                        outlined=True,
                        on_click=State.reset,
                    )
                FileDrop(
                    on_file=State.load_from_file,
                    on_total_progress=lambda *args: None,
                    label="Drag file here",
                )

                if df is not None:
                    columns = list(map(str, df.columns))
                    plottypes = ["scatter", "histogram", "histogram2d"]
                    solara.Select(
                        "Plot type",
                        values=plottypes,
                        value=State.plottype,
                    )
                    if State.plottype.value == "scatter":
                        solara.SliderFloat(label="Size",
                                           value=State.size_max,
                                           min=1,
                                           max=100)
                        solara.Checkbox(label="Log x", value=State.logx)
                        solara.Checkbox(label="Log y", value=State.logy)
                        solara.Checkbox(label="Flip x", value=State.flipx)
                        solara.Checkbox(label="Flip y", value=State.flipy)
                        solara.Select("Column x",
                                      values=columns,
                                      value=State.x)
                        solara.Select("Column y",
                                      values=columns,
                                      value=State.y)
                        solara.Select("Size", values=columns, value=State.size)
                        solara.Select("Color",
                                      values=columns,
                                      value=State.color)
                    elif State.plottype.value == "histogram":
                        solara.SliderInt(
                            label="Number of Bins",
                            value=State.nbins,
                            step=10,
                            min=10,
                            max=1000,
                        )
                        solara.Select("Column x",
                                      values=columns,
                                      value=State.x)
                        solara.Checkbox(label="Logarithmic count",
                                        value=State.logy)
                        solara.Select(
                            label="Normalization",
                            values=State.norms,
                            value=State.norm,
                        )
                    elif State.plottype.value == "histogram2d":
                        solara.SliderInt(
                            label="Number of Bins",
                            value=State.nbins,
                            step=10,
                            min=10,
                            max=1000,
                        )
                        solara.Select("Column x",
                                      values=columns,
                                      value=State.x)
                        solara.Select("Column y",
                                      values=columns,
                                      value=State.y)

    if df is not None:
        with Columns(widths=[2, 4]):
            if State.x.value and State.y.value:
                if State.plottype.value == "scatter":
                    scatterplot()
                elif State.plottype.value == "histogram":
                    histogramplot()
                elif State.plottype.value == "histogram2d":
                    histogram2dplot()
                else:
                    solara.Warning("Select a plot type")
            else:
                solara.Warning("Select x and y columns")

    else:
        solara.Info(
            "No data loaded, click on the sample dataset button to load a sample dataset, or upload a file."
        )

    solara.Button(
        label="View source",
        icon_name="mdi-github-circle",
        attributes={
            "href": github_url,
            "target": "_blank"
        },
        text=True,
        outlined=True,
    )


@solara.component
def Layout(children):
    route, routes = solara.use_route()
    return solara.AppLayout(children=children)
