import numpy as np
import plotly.express as px
import solara as sl
import vaex
from plotly.graph_objs._figurewidget import FigureWidget
from solara.components.columns import Columns

df_sample = vaex.example()


class PlotState:
    """
    Combination of reactive states which instantiate a specific plot's settings/properties
    """

    def __init__(self, type):
        self.flipx = sl.reactive(False)
        self.flipy = sl.reactive(False)


@sl.component()
def aggregate_menu(plotstate):
    with sl.Card():
        with Columns([1, 1]):
            with sl.Column():
                sl.Switch(label="Flip y", value=plotstate.flipy)
            with sl.Column():
                sl.Switch(label="Flip x", value=plotstate.flipx)


@sl.component()
def aggregated(plotstate):
    df = df_sample
    filter, set_filter = sl.use_cross_filter(id(df), "filter-aggregated")

    dff = df
    if filter:
        dff = df[filter]

    def perform_binning():
        expr = (dff.x, dff.y)
        limits = [dff.minmax(dff.x), dff.minmax(dff.y)]

        y = dff.count(
            binby=expr,
            limits=limits,
            shape=100,
            array_type="xarray",
        )

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
        fig.update_xaxes(autorange=False)
        fig.update_yaxes(autorange=False)
        return fig

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    def add_effects(fig_element: sl.Element):

        def set_xflip():
            print("setting xflip", plotstate.flipx.value)
            fig_widget: FigureWidget = sl.get_widget(fig_element)
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
    plotstate = PlotState("aggregated")
    aggregated(plotstate)
    aggregate_menu(plotstate)


if __name__ == "__main__":
    Page()
