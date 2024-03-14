import numpy as np
import plotly.express as px
import solara as sl
import vaex
from plotly.graph_objs._figurewidget import FigureWidget

df_sample = vaex.example()  # happens on any df


class PlotState:
    """Holds flip info"""

    def __init__(self):
        self.flipx = sl.reactive(False)
        self.flipy = sl.reactive(False)


@sl.component()
def menu(plotstate):
    """Switches for flipping"""
    with sl.Card():
        with sl.Columns([1, 1]):
            with sl.Column():
                sl.Switch(label="Flip y", value=plotstate.flipy)
            with sl.Column():
                sl.Switch(label="Flip x", value=plotstate.flipx)


@sl.component()
def scatter(plotstate):
    """Generates scatterplot"""
    df = df_sample

    dff = df

    def create_fig():
        x = dff.x.values
        y = dff.y.values
        fig = px.scatter(x=x, y=y)
        return fig

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    def add_effects(fig_element: sl.Element):

        def set_xflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # flip
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)
            print(fig_widget.layout.xaxis)

        def set_yflip():
            print("setting yflip", plotstate.flipy.value)
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=True)
            print(fig_widget.layout.yaxis)

        sl.use_effect(set_xflip, dependencies=[plotstate.flipx.value])
        sl.use_effect(set_yflip, dependencies=[plotstate.flipy.value])

    fig_el = sl.FigurePlotly(figure)
    add_effects(fig_el)

    return


@sl.component()
def imshow(plotstate):
    """Generates imshow plot with log10 scaling"""
    df = df_sample

    dff = df

    def perform_binning():
        expr = (dff.x, dff.y)
        limits = [dff.minmax(dff.x), dff.minmax(dff.y)]

        y = dff.count(
            binby=expr,
            limits=limits,
            shape=100,
            array_type="xarray",
        )

        # plotly doesn't support nan's -- have to change to -999
        y = np.log10(y)
        y = y.where(np.abs(y) != np.inf, np.nan)
        cmin = float(np.min(y).values)
        cmax = float(np.max(y).values)
        y = y.fillna(-999)
        return y, cmin, cmax

    def create_fig():
        z, cmin, cmax = perform_binning()
        fig = px.imshow(z.T,
                        zmin=cmin,
                        zmax=cmax,
                        origin="lower",
                        color_continuous_scale="inferno")
        return fig

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    def add_effects(fig_element: sl.Element):

        def set_xflip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

            # flip
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)
            print(fig_widget.layout.xaxis)

        def set_yflip():
            print("setting yflip", plotstate.flipy.value)
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=True)
            print(fig_widget.layout.yaxis)

        sl.use_effect(set_xflip, dependencies=[plotstate.flipx.value])
        sl.use_effect(set_yflip, dependencies=[plotstate.flipy.value])

    fig_el = sl.FigurePlotly(figure)
    add_effects(fig_el)

    return


@sl.component()
def Page():
    plotstate = PlotState()
    with sl.Columns([1, 1]):
        imshow(plotstate)
        scatter(plotstate)
    menu(plotstate)


if __name__ == "__main__":
    Page()
