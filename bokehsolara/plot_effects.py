"""Main functions for plot effects"""

from bokeh.models.plots import Plot
import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
from jupyter_bokeh import BokehModel

from plot_actions import (
    change_formatter,
    fetch_data,
    reset_range,
    update_label,
    update_axis,
)
from state import PlotState
from util import check_categorical

__all__ = ["add_effects"]


def add_effects(pfig: rv.ValueElement, plotstate: PlotState, dff, filter,
                layout) -> None:

    def update_x():
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            update_axis(plotstate, fig_model, dff, "x")

    def update_y():
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            update_axis(plotstate, fig_model, dff, "y")

    def update_color():
        """Color data column change update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            with fig_model.hold(render=True):
                z = dff[plotstate.color.value].values
                z = np.log10(z) if plotstate.colorlog.value else z
                fig_model.renderers[0].data_source.data["z"] = z
                fig_model.renderers[0].glyph.fill_color
                fig_model.right[
                    0].color_mapper.palette = plotstate.colorscale.value
                # TODO: fancy title based on bintype
                fig_model.right[0].title = plotstate.color.value

    def update_flipx():
        """X-axis flip update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            # TODO: should we rest both ranges?
            reset_range(plotstate, fig_model, dff, axis="x")
            fig_model.x_range.flipped = plotstate.flipx.value

    def update_flipy():
        """Y-axis flip update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            # TODO: should we rest both ranges?
            reset_range(plotstate, fig_model, dff, axis="y")
            fig_model.y_range.flipped = plotstate.flipx.value

    def update_cmap():
        """Colormap update effect"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            fig_model.right[
                0].color_mapper.palette = plotstate.colorscale.value

    def update_filter():
        """Complete filter update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            # TODO: categorical support with jittering
            x = fetch_data(plotstate, dff, axis="x")
            y = fetch_data(plotstate, dff, axis="y")
            fig_model.renderers[0].data_source.data = dict(
                x=x.values,
                y=y.values,
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
            change_formatter(plotstate, fig_model, axis="x")
            update_label(plotstate, fig_model, axis="x")
            reset_range(plotstate, fig_model, dff, axis="x")

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
            change_formatter(plotstate, fig_model, axis="y")
            update_label(plotstate, fig_model, axis="y")
            reset_range(plotstate, fig_model, dff, axis="y")

    def update_height():
        """Height linking callback, because auto-sizing doesn't work"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            fig_model.height = layout["h"] * 45 - 90
            print(fig_model.height)

    sl.use_effect(update_filter, dependencies=[filter])
    sl.use_effect(update_height, dependencies=[layout["h"]])
    sl.use_effect(update_x, dependencies=[plotstate.x.value])
    sl.use_effect(update_y, dependencies=[plotstate.y.value])
    sl.use_effect(update_color, dependencies=[plotstate.color.value])
    sl.use_effect(update_cmap, dependencies=[plotstate.colorscale.value])
    sl.use_effect(update_flipx, dependencies=[plotstate.flipx.value])
    sl.use_effect(update_flipy, dependencies=[plotstate.flipy.value])
    sl.use_effect(update_logx, dependencies=[plotstate.logx.value])
    sl.use_effect(update_logy, dependencies=[plotstate.logy.value])
    return
