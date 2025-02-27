"""Main functions for plot effects"""

import asyncio
from bokeh.models.plots import Plot
import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
from jupyter_bokeh import BokehModel

from plot_actions import (
    update_tooltips,
    change_formatter,
    fetch_data,
    reset_range,
    update_label,
    update_axis,
    aggregate_data,
    update_coloraxis,
)
from state import PlotState
from util import check_categorical

__all__ = ["add_scatter_effects", "add_heatmap_effects"]


def add_scatter_effects(pfig: rv.ValueElement, plotstate: PlotState, dff,
                        filter) -> None:
    """Scatter-glyph specific effects"""

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
            update_coloraxis(plotstate, fig_model, dff)

    def update_cmap():
        """Colormap update effect"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model

            with fig_model.hold(render=True):
                fig_model.right[
                    0].color_mapper.palette = plotstate.colorscale.value
                fig_model.renderers[0].glyph.fill_color[
                    "transform"].palette = plotstate.colorscale.value

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

    sl.use_effect(update_filter, dependencies=[filter])
    sl.use_effect(update_x, dependencies=[plotstate.x.value])
    sl.use_effect(update_y, dependencies=[plotstate.y.value])
    sl.use_effect(update_color, dependencies=[plotstate.color.value])
    sl.use_effect(update_cmap, dependencies=[plotstate.colorscale.value])
    return


def add_common_effects(
    pfig: rv.ValueElement,
    plotstate: PlotState,
    layout,
):
    """Adds common effects across plots.

    Specifically adds flips, logs, and height resizing.

    Args:
        pfig: figure element
        plotstate: plot variables
        layout: grid layout dictionary for the card.
    """

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

    def update_height():
        """Height linking callback, because auto-sizing doesn't work. Only runs if debounce completes"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model = fig_widget._model
            with fig_model.hold(render=True):
                if debounced_height.finished:
                    if height == debounced_height.value:
                        fig_model.height = debounced_height.value

    def get_height():
        return layout["h"] * 45 - 90

    height = sl.use_memo(get_height, dependencies=[layout["h"]])

    async def debounce_height():
        await asyncio.sleep(0.05)
        return height

    debounced_height = sl.lab.use_task(debounce_height, dependencies=[height])
    try:
        sl.use_effect(update_height, dependencies=[debounced_height.finished])
        sl.use_effect(update_flipx, dependencies=[plotstate.flipx.value])
        sl.use_effect(update_flipy, dependencies=[plotstate.flipy.value])
        if plotstate.plottype != "heatmap":
            sl.use_effect(update_logx, dependencies=[plotstate.logx.value])
            sl.use_effect(update_logy, dependencies=[plotstate.logy.value])
    except Exception as e:
        print("effect bind error", e)


def add_heatmap_effects(pfig: rv.ValueElement, plotstate: PlotState, dff,
                        filter) -> None:
    """Heatmap (rect glyph) specific effects"""

    def update_data():
        """X/Y/Color data column change update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            with fig_model.hold(render=True):
                z, x_centers, y_centers, limits = aggregate_data(
                    plotstate, dff)
                print("effect, z from return", len(z.flatten()))

                source = fig_model.renderers[0].data_source
                source.data = {
                    "x": np.repeat(x_centers, len(y_centers)),
                    "y": np.tile(y_centers, len(x_centers)),
                    "z": z.flatten(),
                }
                fig_model.renderers[0].glyph.update(
                    height=(limits[0][1] - limits[0][0]) /
                    plotstate.nbins.value,
                    width=(limits[1][1] - limits[1][0]) /
                    plotstate.nbins.value,
                )
                for axis in {"x", "y"}:
                    update_label(plotstate, fig_model,
                                 axis=axis)  # update all labels
                update_tooltips(plotstate, fig_model)
            update_coloraxis(plotstate, fig_model,
                             dff)  # also update coloraxis

    def update_filter():
        """Filter update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            with fig_model.hold(render=True):
                z, x_centers, y_centers, limits = aggregate_data(
                    plotstate, dff)
                source = fig_model.renderers[0].data_source
                source.data = {
                    "x": np.repeat(x_centers, len(y_centers)),
                    "y": np.tile(y_centers, len(x_centers)),
                    "z": z.flatten(),
                }

    def update_color():
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            update_coloraxis(plotstate, fig_model, dff)

    def update_cmap():
        """Colormap update effect"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            fig_model.right[
                0].color_mapper.palette = plotstate.colorscale.value

    sl.use_effect(update_filter, dependencies=[filter])
    sl.use_effect(
        update_data,
        dependencies=[plotstate.x.value, plotstate.y.value],
    )
    sl.use_effect(
        update_color,
        dependencies=[
            plotstate.color.value,
            plotstate.colorlog.value,
            plotstate.bintype.value,
        ],
    )
    sl.use_effect(update_cmap, dependencies=[plotstate.colorscale.value])
