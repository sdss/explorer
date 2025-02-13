"""Main function for plot effects"""

from bokeh.models.formatters import CustomJSTickFormatter
from bokeh.models.plots import Plot
from bokeh.models import BasicTickFormatter, LogTickFormatter
import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
from jupyter_bokeh import BokehModel

from plot_utils import (
    calculate_range,
    generate_xlabel,
    generate_ylabel,
    map_categorical_data,
)
from util import check_categorical

__all__ = ["add_effects"]


# TODO: check if dff + plotstate synced????
def add_effects(pfig: rv.ValueElement, plotstate, dff, filter, layout) -> None:

    def update_x():
        # TODO: ensure no catagorical data failure
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            if check_categorical(plotstate.x.value):
                x, mapping, formatter = map_categorical_data(
                    dff[plotstate.x.value])
                x = x.values
                fig_model.below[0].formatter = formatter
            else:
                x = dff[plotstate.x.value].values
                fig_model.below[0].formatter = (BasicTickFormatter()
                                                if not plotstate.logx.value
                                                else LogTickFormatter())
            newrange = calculate_range(plotstate, dff, col="x")
            with fig_model.hold(render=True):
                fig_model.renderers[0].data_source.data["x"] = x  # set data
                fig_model.below[0].axis_label = generate_xlabel(
                    plotstate)  # set label
                fig_model.x_range.update(start=newrange[0],
                                         end=newrange[1])  # update range

    def update_y():
        # TODO: ensure no catagorical data failure
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            y = dff[plotstate.y.value].values
            fig_model.renderers[0].data_source.data["y"] = y
            fig_model.left[0].axis_label = generate_ylabel(plotstate)

    def update_color():
        """Color data column change update"""
        # TODO: ensure no catagorical data failure
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            with fig_model.hold(render=True):
                z = dff[plotstate.color.value].values
                z = np.log10(z) if plotstate.colorlog.value else z
                fig_model.renderers[0].data_source.data["z"] = z
                fig_model.renderers[0].glyph.fill_color
                fig_model.right[
                    0].color_mapper.palette = plotstate.colormap.value
                # TODO: fancy title based on bintype
                fig_model.right[0].title = plotstate.color.value

    def update_flipx():
        """X-axis flip update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            # TODO: catagorical support
            newrange = calculate_range(plotstate, dff, col="x")
            fig_model.x_range.update(start=newrange[0], end=newrange[1])

            fig_model.x_range.flipped = plotstate.flipx.value

    def update_flipy():
        """Y-axis flip update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            # TODO: catagorical support
            newrange = calculate_range(plotstate, dff, col="y")
            fig_model.y_range.update(start=newrange[0], end=newrange[1])

            fig_model.y_range.flipped = plotstate.flipx.value

    def update_cmap():
        """Colormap update effect"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            fig_model.right[0].color_mapper.palette = plotstate.colormap.value

    def update_filter():
        """Complete filter update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            # TODO: categorical support with jittering
            x = dff[plotstate.x.value].values
            y = dff[plotstate.y.value].values
            fig_model.renderers[0].data_source.data = dict(
                x=x,
                y=y,
                z=dff[plotstate.color.value].values,
                sdss_id=dff["L"].values,
            )

    def update_logx():
        """X-axis log scale callback"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            if plotstate.logx.value and not check_categorical(
                    plotstate.x.value):
                fig_model.x_scale = fig_model.extra_x_scales["log"]
            else:
                fig_model.x_scale = fig_model.extra_x_scales["lin"]
            fig_model.below[0].axis_label = generate_xlabel(plotstate)
            # TODO: fix tickers
            newrange = calculate_range(plotstate, dff, col="x")
            fig_model.x_range.update(start=newrange[0], end=newrange[1])

    def update_logy():
        """Y-axis log scale callback"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            if plotstate.logy.value and not check_categorical(
                    plotstate.y.value):
                fig_model.y_scale = fig_model.extra_y_scales["log"]
            else:
                fig_model.y_scale = fig_model.extra_y_scales["lin"]
            fig_model.left[0].axis_label = generate_ylabel(plotstate)
            # TODO: fix tickers
            newrange = calculate_range(plotstate, dff, col="y")
            fig_model.y_range.update(start=newrange[0], end=newrange[1])

    def update_height():
        """Height linking callback, because auto-sizing doesn't work"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            fig_model.height = layout["h"] * 45 - 90

    sl.use_effect(update_filter, dependencies=[filter])
    sl.use_effect(update_height, dependencies=[layout["h"]])
    sl.use_effect(update_x, dependencies=[plotstate.x.value])
    sl.use_effect(update_y, dependencies=[plotstate.y.value])
    sl.use_effect(update_color, dependencies=[plotstate.color.value])
    sl.use_effect(update_cmap, dependencies=[plotstate.colormap.value])
    sl.use_effect(update_flipx, dependencies=[plotstate.flipx.value])
    sl.use_effect(update_flipy, dependencies=[plotstate.flipy.value])
    sl.use_effect(update_logx, dependencies=[plotstate.logx.value])
    sl.use_effect(update_logy, dependencies=[plotstate.logy.value])
    return
