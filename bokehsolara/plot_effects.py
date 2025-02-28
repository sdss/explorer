"""Main functions for plot effects"""

import asyncio
import operator
from functools import reduce
import logging
from bokeh.models.plots import Plot
from bokeh.models import BooleanFilter, Rect
import numpy as np
import vaex as vx
import reacton.ipyvuetify as rv
import solara as sl
from jupyter_bokeh import BokehModel

from plot_actions import (
    update_color_mapper,
    update_mapping,
    update_tooltips,
    change_formatter,
    fetch_data,
    reset_range,
    update_label,
    update_axis,
    aggregate_data,
)
from state import PlotState
from util import check_categorical

__all__ = [
    "add_scatter_effects",
    "add_heatmap_effects",
    "add_common_effects",
    "add_histogram_effects",
]

logger = logging.getLogger()  # TODO


def add_common_effects(
    pfig: rv.ValueElement,
    plotstate: PlotState,
    dff: vx.DataFrame,
    layout,
):
    """Adds common effects across plots.

    Specifically adds flips, logs, and height resizing.

    Args:
        pfig: figure element
        plotstate: plot variables
        dff: filtered dataframe
        layout: grid layout dictionary for the card. used for triggering height effect
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
            if plotstate.plottype == "histogram":
                if plotstate.logy.value:
                    fig_model.y_scale = fig_model.extra_y_scales["log"]
                else:
                    fig_model.y_scale = fig_model.extra_y_scales["lin"]
            elif plotstate.logy.value and not check_categorical(
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
            reset_range(plotstate, fig_model, dff, axis="x")
            fig_model.x_range.flipped = plotstate.flipx.value

    def update_flipy():
        """Y-axis flip update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            reset_range(plotstate, fig_model, dff, axis="y")
            fig_model.y_range.flipped = plotstate.flipy.value

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

    debounced_height = sl.lab.use_task(debounce_height,
                                       dependencies=[height],
                                       prefer_threaded=False)
    try:
        sl.use_effect(update_height, dependencies=[debounced_height.finished])
        sl.use_effect(update_flipx, dependencies=[plotstate.flipx.value])
        if plotstate.plottype != "histogram":
            sl.use_effect(update_flipy, dependencies=[plotstate.flipy.value])
        if plotstate.plottype != "heatmap":
            sl.use_effect(update_logx, dependencies=[plotstate.logx.value])
            sl.use_effect(update_logy, dependencies=[plotstate.logy.value])
    except Exception as e:
        print("effect bind error", e)


def add_scatter_effects(
    pfig: rv.ValueElement,
    plotstate: PlotState,
    dff,
    filter,
    local_filter,
    debounced_local_filter,
) -> None:
    """Scatter-glyph specific effects

    Args:
        pfig: figure element
        plotstate: plot variables
        dff: filtered dataframe
        filter: filter object, for use in triggering effects
    """

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
            update_axis(plotstate, fig_model, dff, "color")

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
            alls = [filter]
            if debounced_local_filter.value == local_filter.value:
                alls.append(debounced_local_filter)
            filters = [f for f in alls if f is not None]
            if filters:
                fig_model.renderers[0].view.filter.booleans = (reduce(
                    operator.and_, filters[1:],
                    filters).values.to_numpy().astype("bool"))
            else:
                fig_model.renderers[0].view.filter.booleans = None

    sl.use_effect(update_filter,
                  dependencies=[dff, filter, debounced_local_filter.finished])
    sl.use_effect(update_x, dependencies=[plotstate.x.value])
    sl.use_effect(update_y, dependencies=[plotstate.y.value])
    sl.use_effect(
        update_color,
        dependencies=[plotstate.color.value, plotstate.logcolor.value])
    sl.use_effect(update_cmap, dependencies=[plotstate.colorscale.value])
    return


def add_heatmap_effects(pfig: rv.ValueElement, plotstate: PlotState, dff,
                        filter) -> None:
    """Heatmap (rect glyph) specific effects

    Args:
        pfig: figure element
        plotstate: plot variables
        dff: filtered dataframe
        filter: filter object, for use in triggering effects
    """

    def update_data():
        """X/Y/Color data column change update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            try:
                assert len(dff) > 0
                color, x_centers, y_centers, widths = aggregate_data(
                    plotstate, dff)
            except Exception as e:
                logger.debug("0 length, leaving")
                print("exception on update_data", e)
                # TODO: Alert.update('Your data is too small to aggregate! Not updating.',color='warning')
                return
            with fig_model.hold(render=True):
                source = fig_model.renderers[0].data_source
                fill_color = fig_model.renderers[0].glyph.fill_color
                source.data = {
                    "x": np.repeat(x_centers, len(y_centers)),
                    "y": np.tile(y_centers, len(x_centers)),
                    "color": color.flatten(),
                }
                # NOTE: you have to remake the glyph because the height/width prop doesn't update on the render
                glyph = Rect(
                    x="x",
                    y="y",
                    width=widths[0],
                    height=widths[1],
                    dilate=True,
                    line_color=None,
                    fill_color=fill_color,
                )
                fig_model.add_glyph(source, glyph)
                fig_model.renderers = fig_model.renderers[1:]
                for axis in ("x", "y"):
                    update_label(plotstate, fig_model,
                                 axis=axis)  # update all labels
                    reset_range(plotstate, fig_model, dff, axis=axis)
                update_tooltips(plotstate, fig_model)

    def update_color():
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            try:
                color = aggregate_data(plotstate, dff)[0]
            except AssertionError:
                logger.debug("attempted exit, leaving")
                # TODO: Alert.update('Your data is too small to aggregate! Not updating.',color='warning')
                return
            with fig_model.hold(render=True):
                fig_model.renderers[0].data_source.data[
                    "color"] = color.flatten()
                update_color_mapper(plotstate, fig_model, color)
                change_formatter(plotstate,
                                 fig_model,
                                 axis="color",
                                 color=color)
                update_label(plotstate, fig_model, axis="color")
                update_tooltips(plotstate, fig_model)

    def update_cmap():
        """Colormap update effect"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            fig_model.right[
                0].color_mapper.palette = plotstate.colorscale.value

    sl.use_effect(
        update_data,
        dependencies=[
            plotstate.x.value,
            plotstate.y.value,
            plotstate.nbins.value,
            filter,
        ],
    )
    sl.use_effect(
        update_color,
        dependencies=[
            plotstate.color.value,
            plotstate.logcolor.value,
            plotstate.bintype.value,
        ],
    )
    sl.use_effect(update_cmap, dependencies=[plotstate.colorscale.value])


def add_histogram_effects(pfig: rv.ValueElement, plotstate: PlotState, dff,
                          filter) -> None:
    """Histogram (quad glyph) specific effects

    Args:
        pfig: figure element
        plotstate: plot variables
        dff: filtered dataframe
        filter: filter object, for use in triggering effects
    """

    def update_data():
        """X/Y/Color data column change update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            if check_categorical(dff[plotstate.x.value]):
                update_mapping(plotstate, axis="x")
            try:
                assert len(dff) > 0
                centers, edges, counts = aggregate_data(plotstate, dff)
            except Exception as e:
                logger.debug("0 length, leaving")
                print("exception on update_data", e)
                # TODO: Alert.update('Your data is too small to aggregate! Not updating.',color='warning')
                return
            with fig_model.hold(render=True):
                fig_model.renderers[0].data_source.data = {
                    "centers": centers,
                    "left": edges[:-1],
                    "right": edges[1:],
                    "y": counts,
                }
                for axis in ("x", "y"):
                    update_label(plotstate, fig_model,
                                 axis=axis)  # update all labels
                    reset_range(plotstate, fig_model, dff, axis=axis)
                update_tooltips(plotstate, fig_model)

    sl.use_effect(
        update_data,
        dependencies=[
            plotstate.x.value,
            plotstate.nbins.value,
            filter,
        ],
    )
