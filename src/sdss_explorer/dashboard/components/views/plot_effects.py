"""Main functions for plot effects"""

import asyncio
import logging
from bokeh.models.plots import Plot
from bokeh.models import ColumnDataSource, Rect
import numpy as np
import vaex as vx
import reacton.ipyvuetify as rv
import solara as sl
from jupyter_bokeh import BokehModel

from .plot_actions import (
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
from .plot_utils import check_categorical
from ...dataclass import PlotState, Alert, SubsetState, State

__all__ = [
    "add_scatter_effects",
    "add_heatmap_effects",
    "add_common_effects",
    "add_histogram_effects",
]

logger = logging.getLogger("dashboard")


def add_common_effects(
    pfig: rv.ValueElement,
    source: ColumnDataSource,
    plotstate: PlotState,
    dff: vx.DataFrame,
    set_filter,
    layout,
):
    """Adds common effects across plots.

    Specifically adds flips, logs, and height resizing.

    Args:
        pfig: figure element
        plotstate: plot variables
        source: CDS object, for binding
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
            change_formatter(plotstate, fig_model, dff, axis="x")
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
            change_formatter(plotstate, fig_model, dff, axis="y")
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

    # selection callback to update the filter object
    df = SubsetState.subsets.value[plotstate.subset.value].df

    def bind_crossmatch():

        def propogate_select_to_filter(attr, old, new):
            if len(new) > 0:
                logger.debug("starting filter operation")
                if plotstate.plottype == "histogram":
                    # NOTE: numpy arrays
                    if check_categorical(plotstate.x.value):
                        data = source.data["centers"][new]
                        dataExpr = df[plotstate.x.value].map(
                            plotstate.xmapping)
                        logger.debug(f"hist: {str(dataExpr)}")
                        set_filter(dataExpr.isin(data))
                    else:
                        data = source.data["centers"][new]
                        col = plotstate.x.value
                        xmin = np.nanmin(data)
                        xmax = np.nanmax(data)
                        logger.debug(
                            f"hist: (({col}>={xmin})&({col}<={xmax}))")
                        set_filter(df[f"(({col}>={xmin})&({col}<={xmax}))"])

                elif plotstate.plottype == "heatmap":
                    # NOTE: numpy arrays
                    datax = source.data["x"][new]
                    datay = source.data["y"][new]
                    if check_categorical(plotstate.x.value):
                        colx = df[plotstate.x.value].map(plotstate.xmapping)
                        xfilter = colx.isin(datax)
                    else:
                        colx = plotstate.x.value
                        xmin = np.nanmin(datax)
                        xmax = np.nanmax(datax)
                        xfilter = (df[colx] >= xmin) & (df[colx] <= xmax)
                    if check_categorical(plotstate.y.value):
                        coly = df[plotstate.y.value].map(plotstate.ymapping)
                        yfilter = coly.isin(datay)
                    else:
                        coly = plotstate.y.value
                        ymin = np.nanmin(datay)
                        ymax = np.nanmax(datay)
                        yfilter = (df[coly] >= ymin) & (df[coly] <= ymax)
                    combined = xfilter & yfilter
                    logger.debug(f"heatmap: {str(combined)}")
                    set_filter(combined)

                elif plotstate.plottype == "scatter":
                    # NOTE: pyarrow ChunkedArrays
                    datax = source.data["x"].take(new)
                    datay = source.data["y"].take(new)
                    colx = plotstate.x.value
                    coly = plotstate.y.value
                    newfilter = (df[colx].isin(datax)) & (df[coly].isin(datay))
                    logger.debug(f"scatter: {str(newfilter)}")
                    set_filter(newfilter)
            else:
                logger.debug("unsetting filter")
                set_filter(None)

        source.selected.on_change("indices", propogate_select_to_filter)

        def cleanup():
            source.selected.remove_on_change("indices",
                                             propogate_select_to_filter)
            source.selected.indices = []

        return cleanup

    sl.use_effect(bind_crossmatch, dependencies=[df])

    try:
        sl.use_effect(update_height, dependencies=[debounced_height.finished])
        sl.use_effect(update_flipx, dependencies=[plotstate.flipx.value])
        if plotstate.plottype != "histogram":
            sl.use_effect(update_flipy, dependencies=[plotstate.flipy.value])
        if plotstate.plottype != "heatmap":
            sl.use_effect(update_logx, dependencies=[plotstate.logx.value])
            sl.use_effect(update_logy, dependencies=[plotstate.logy.value])
    except Exception as e:
        logger.error("main effect bind error", e)


def add_scatter_effects(
    pfig: rv.ValueElement,
    plotstate: PlotState,
    dff: vx.DataFrame,
    filter,
) -> None:
    """Scatter-glyph specific effects

    Args:
        pfig: figure element
        plotstate: plot variables
        dff: filtered dataframe
        filter: filter object, for use in triggering effects
    """
    df = SubsetState.subsets.value[plotstate.subset.value].df

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
                newmap = plotstate.Lookup["colorscales"][
                    plotstate.colorscale.value]
                fig_model.right[0].color_mapper.palette = newmap
                fig_model.renderers[
                    0].glyph.fill_color.transform.palette = newmap

    def update_filter():
        """Complete filter update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            if dff is not None:
                x = fetch_data(plotstate, dff, axis="x")
                y = fetch_data(plotstate, dff, axis="y")
                color = fetch_data(plotstate, dff, axis="color")
                fig_model.renderers[0].data_source.data = dict(
                    x=x.values,
                    y=y.values,
                    color=color.values,
                    sdss_id=dff["sdss_id"].values,
                )
                update_color_mapper(plotstate, fig_model, dff)
                change_formatter(plotstate, fig_model, dff, axis="color")

    sl.use_effect(update_filter, dependencies=[df, dff])
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
    df = SubsetState.subsets.value[plotstate.subset.value].df

    def update_data():
        """X/Y/Color data column change update"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            if dff is not None:
                try:
                    assert len(dff) > 0
                    color, x_centers, y_centers, widths = aggregate_data(
                        plotstate, dff)
                except Exception as e:
                    logger.debug("exception on update_data (heatmap):" +
                                 str(e))
                    Alert.update(
                        "Your data is too small to aggregate! Not updating heatmap.",
                        color="warning",
                    )
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

                    # update all labels, ranges, etc
                    for axis in ("x", "y"):
                        update_label(plotstate, fig_model, axis=axis)
                        change_formatter(plotstate, fig_model, dff, axis=axis)
                        reset_range(plotstate, fig_model, dff, axis=axis)
                    update_color_mapper(plotstate, fig_model, dff, color)
                    change_formatter(plotstate,
                                     fig_model,
                                     dff,
                                     axis="color",
                                     color=color)
                    update_tooltips(plotstate, fig_model)

    def update_color():
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            if dff is not None:
                try:
                    color = aggregate_data(plotstate, dff)[0]
                except AssertionError as e:
                    logger.debug("color update failed (heatmap)" + str(e))
                    Alert.update(
                        "Your data is too small to aggregate! Not updating heatmap.",
                        color="warning",
                    )
                    return
                with fig_model.hold(render=True):
                    fig_model.renderers[0].data_source.data[
                        "color"] = color.flatten()
                    update_color_mapper(plotstate, fig_model, dff, color)
                    change_formatter(plotstate,
                                     fig_model,
                                     dff,
                                     axis="color",
                                     color=color)
                    update_label(plotstate, fig_model, axis="color")
                    update_tooltips(plotstate, fig_model)

    def update_cmap():
        """Colormap update effect"""
        fig_widget: BokehModel = sl.get_widget(pfig)
        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            newmap = plotstate.Lookup["colorscales"][
                plotstate.colorscale.value]
            fig_model.right[0].color_mapper.palette = newmap
            fig_model.renderers[0].glyph.fill_color.transform.palette = newmap

    sl.use_effect(
        update_data,
        dependencies=[
            df,
            dff,
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
    df = SubsetState.subsets.value[plotstate.subset.value].df

    def update_data():
        """X/Y/Color data column change update"""
        fig_widget: BokehModel = sl.get_widget(pfig)

        if isinstance(fig_widget, BokehModel):
            fig_model: Plot = fig_widget._model
            try:
                if check_categorical(dff[plotstate.x.value]):
                    update_mapping(plotstate, axis="x")
                assert len(dff) > 0, "zero length dataframe"
                centers, edges, counts = aggregate_data(plotstate, dff)
            except Exception as e:
                logger.debug("exception on update_data (hist):" + str(e))
                Alert.update(f"Data update failed on histogram! {e}",
                             color="warning")
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
                change_formatter(plotstate, fig_model, dff, axis="x")
                update_tooltips(plotstate, fig_model)

    sl.use_effect(
        update_data,
        dependencies=[
            df,
            dff,
            plotstate.x.value,
            plotstate.nbins.value,
            filter,
        ],
    )
