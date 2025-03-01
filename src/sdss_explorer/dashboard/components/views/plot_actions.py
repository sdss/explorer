"""Plot specific actions that are used in effects"""

import logging
from bokeh.models.tools import HoverTool
from typing import Optional
import numpy as np
import vaex as vx
from numpy import ndarray
from bokeh.models import Plot
from bokeh.models.formatters import (
    LogTickFormatter,
    BasicTickFormatter,
)

from ...dataclass import PlotState, State, Alert
from .plot_utils import (
    check_categorical,
    _calculate_color_range,
    calculate_colorbar_ticks,
    calculate_range,
    generate_label,
    generate_datamap,
    generate_categorical_tick_formatter,
    generate_categorical_hover_formatter,
    generate_tooltips,
)

logger = logging.getLogger("dashboard")


def update_tooltips(plotstate: PlotState, fig_model: Plot) -> None:
    """Updates tooltips on toolbar's HoverTool

    Note:
        This will fetch mappings, so it assumes it has already been generated.

    Args:
        plotstate: plot vars
        fig_model: plot object
    """
    # find the tool
    for tool in fig_model.toolbar.tools:
        if isinstance(tool, HoverTool):
            tool.tooltips = generate_tooltips(plotstate)
            if plotstate.plottype == "histogram":
                tool.formatters = {
                    "@centers":
                    generate_categorical_hover_formatter(plotstate, axis="x"),
                }
            else:
                tool.formatters = {
                    "$snap_x":
                    generate_categorical_hover_formatter(plotstate, axis="x"),
                    "$snap_y":
                    generate_categorical_hover_formatter(plotstate, axis="y"),
                    "@color":
                    generate_categorical_hover_formatter(plotstate,
                                                         axis="color"),
                }


def update_axis(
    plotstate: PlotState,
    fig_model: Plot,
    dff: vx.DataFrame,
    axis: str = "x",
):
    """Direct and complete axis update.

    Args:
        plotstate: plot variables
        fig_model: figure object
        dff: filtered dataframe
    """
    # get all attributes of plotstate + fig_model
    assert axis in ("x", "y", "color"), (
        f"expected axis 'x','y', or 'color' but got {axis}")
    col = getattr(plotstate, axis).value  # column name
    try:
        # update before datafetch
        if check_categorical(col):
            update_mapping(plotstate, axis=axis)
        colData = fetch_data(plotstate, dff, axis=axis)
    except Exception as e:
        logger.debug("fetch update" + str(e))
        Alert.update(f"Color update failed! {e}", color="warning")
        return
    with fig_model.hold(render=True):
        fig_model.renderers[0].data_source.data[
            axis] = colData.values  # set data
        change_formatter(plotstate, fig_model, dff,
                         axis=axis)  # change formatter to cat if needed
        update_label(plotstate, fig_model, axis=axis)
        reset_range(plotstate, fig_model, dff, axis=axis)
        update_tooltips(plotstate, fig_model)


def reset_range(plotstate: PlotState,
                fig_model: Plot,
                dff: vx.DataFrame,
                axis: str = "x"):
    """Resets given axis range on a figure model.

    Args:
        plotstate: plot variables
        fig_model: figure object
        axis: axis to update for. 'x', 'y', or 'color'.

    Returns:
        newrange: tuple of new range values, only in x/y resets

    """
    assert axis in ("x", "y", "color"), f"expected axis x or y but got {axis}"
    if dff is not None:
        if (plotstate.plottype == "histogram") and (axis == "y"):
            _reset_histogram_yrange(plotstate, fig_model, dff)
        elif axis == "color":
            update_color_mapper(plotstate, fig_model, dff)
        else:
            datarange = getattr(fig_model, f"{axis}_range")
            # NOTE: flip/log is automatically by the calculation function
            newrange = calculate_range(plotstate, dff, axis=axis)
            datarange.update(start=newrange[0], end=newrange[1])
            return newrange


def _reset_histogram_yrange(plotstate: PlotState, fig_model: Plot,
                            dff: vx.DataFrame):
    """Helper for histogram y-range reset.

    Args:
        plotstate: plot variables
        fig_model: figure object
        dff: filtered dataframe
    """
    _, __, counts = aggregate_data(plotstate, dff)
    start = 0 if not plotstate.logy.value else 1
    end = counts.max() * 1.2
    fig_model.renderers[0].glyph.bottom = start
    fig_model.y_range.update(start=start, end=end)


def update_label(plotstate: PlotState,
                 fig_model: Plot,
                 axis: str = "x") -> None:
    """
    Updates label for axis, regenerating as needed

    Args:
        plotstate: plot variables
        fig_model: figure object
        axis: axis to update for. 'x', 'y', or 'color'
    """
    assert axis in ("x", "y", "color"), f"expected axis x or y but got {axis}"

    # gangsta one liner
    loc = ("below" if axis == "x" else "left") if axis != "color" else "right"

    # get place and set it
    ax = getattr(fig_model, loc)[0]
    setattr(
        ax,
        "title" if axis == "color" else "axis_label",
        generate_label(plotstate, axis=axis),
    )


def update_mapping(plotstate: PlotState, axis: str = "x") -> None:
    """Updates the categorical datamapping for the given axis

    Args:
        plotstate: plot variables
        axis: axis to perform update on. any of 'x', 'y', or 'color'

    """
    from state import df  # WARNING: this df must be from SubsetState.subsets later

    assert axis in ("x", "y", "color"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    assert df[col].nunique() < 10, (
        "this column has too many unique categories. not supported.")

    mapping = generate_datamap(df[col])
    setattr(plotstate, f"{axis}mapping", mapping)  # categorical datamap
    return


def update_color_mapper(
    plotstate: PlotState,
    fig_model: Plot,
    dff: vx.DataFrame,
    color: Optional[ndarray] = None,
) -> None:
    """Updates low/high property of color mapper

    Args:
        plotstate: plot variables
        fig_model: plot object to update
        dff: filtered dataframe
        color: optional pre-computed aggregation data.
    """

    low, high = _calculate_color_range(plotstate, dff, color)
    mapper = fig_model.right[0].color_mapper  # same obj as in glyph
    mapper.update(low=low, high=high)
    mapper = fig_model.renderers[
        0].glyph.fill_color.transform  # same obj as in glyph
    mapper.update(low=low, high=high)

    return


def change_formatter(
    plotstate: PlotState,
    fig_model: Plot,
    dff: vx.DataFrame,
    axis: str = "x",
    color: Optional[np.ndarray] = None,
) -> None:
    """
    Updates the formatter on the plot, changing to a categorical type if needed.

    Args:
        plotstate: plot variables
        fig_model: figure object
        axis: axis to update. any of 'x', 'y', or 'color'
        dff: filtered dataframe
    """
    assert axis in ("x", "y", "color"), f"expected axis x or y but got {axis}"

    col = getattr(plotstate, axis).value  # column name
    log = getattr(plotstate, f"log{axis}").value  # whether log
    mapping = getattr(plotstate, f"{axis}mapping")  # categorical datamap

    # gangsta one liner
    loc = ("below" if axis == "x" else "left") if axis != "color" else "right"

    # get place and set it
    ax = getattr(fig_model, loc)[0]
    if (plotstate.plottype == "histogram") and (axis == "y"):
        formatter = BasicTickFormatter()
    else:
        if check_categorical(col):
            formatter = generate_categorical_tick_formatter(mapping)
        else:
            formatter = (LogTickFormatter() if
                         (log and (axis != "color")) else BasicTickFormatter())
    if axis == "color":
        if check_categorical(col):
            ax.ticker.ticks = [v for v in mapping.values()]
            ax.major_label_overrides = {v: k for k, v in mapping.items()}
        else:
            low, high = _calculate_color_range(plotstate, dff=dff, color=color)
            ax.ticker.ticks = calculate_colorbar_ticks(low, high)
            ax.major_label_overrides = {0: "0"}
    else:
        ax.formatter = formatter


def fetch_data(plotstate: PlotState,
               dff: vx.DataFrame,
               axis: str = "x") -> vx.Expression:
    """Helper function to get data and apply mappings if necessary

    Args:
        plotstate: plot variables
        fig_model: figure object
        axis: axis to fetch for. either 'x', 'y', or 'color'.

    Returns:
        Expression of mapped categorical data or raw expression.

    Raises:
        AssertionError: if unexpected axis
        ValueError: if all nan in color

    """
    assert axis in ("x", "y", "color"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    if check_categorical(col):
        # NOTE: we always ensure this is altered prior to fetch
        mapping = getattr(plotstate, f"{axis}mapping")  # categorical datamap
        colData = dff[col].map(mapping)
    else:
        if (axis == "color") and plotstate.logcolor.value:
            colData = np.log10(dff[col])
            try:
                test = colData.values
                test[np.abs(test) == np.inf] = np.nan
                assert not np.all(np.isnan(test))
            except AssertionError:
                raise ValueError(
                    "taking log of color gives no data, not updating.")
        else:
            colData = dff[col]
    return colData


def aggregate_data(
    plotstate: PlotState, dff: vx.DataFrame
) -> (tuple[ndarray, ndarray, ndarray, list[list[float]]]
      | tuple[ndarray, ndarray, ndarray]):
    """
    Create aggregated data expressions for heatmap and histogram

    Args:
        plotstate: plot variables
        dff: filtered dataframe

    Returns:
        color (numpy.ndarray): 2D aggregated data according to `plotstate.bintype`
        x_edges: 1D array of x-axis coordinates
        y_edges: 1D array of x-axis coordinates
        limits: splatted list of x and y axis limits

    Raises:
        ValueError: if no bintype (somehow)
        RuntimeError: if binning is too small (stride bug)
        AssertionError: if data is invalid (all nan, etc)

    """
    # check validity
    if plotstate.bintype.value not in plotstate.Lookup["bintypes"]:
        raise ValueError(
            "no assigned bintype for aggregation. bug somewhere in settings.")

    if plotstate.plottype == "histogram":
        if check_categorical(dff[plotstate.x.value]):
            update_mapping(plotstate, axis="x")
            nbins = len(plotstate.xmapping)
        else:
            nbins = plotstate.nbins.value
        expr = fetch_data(plotstate, dff, axis="x")

        # get bin center and edges; center mainly for us
        if check_categorical(dff[plotstate.x.value]):
            centers = expr.unique(array_type="numpy")
            edges = np.arange(0, expr.nunique() + 1, 1) - 0.5  # offset
        else:
            try:
                limits = expr.minmax()
            except Exception:  # stride bug catch
                limits = [expr.min()[()], expr.max()[()]]
            edges = dff.bin_edges(expr, limits=limits, shape=nbins)
            centers = dff.bin_centers(expr, limits=limits, shape=nbins)

        # get counts
        if check_categorical(dff[plotstate.x.value]):
            series = expr.value_counts()  # value_counts as in Pandas
            counts = series.values
        else:
            counts = dff.count(binby=expr,
                               shape=nbins,
                               delay=True,
                               array_type="numpy")
            dff.execute()
            counts = counts.get().flatten()

        return centers, edges, counts

    elif plotstate.plottype == "heatmap":
        # update mappings if needed
        if check_categorical(dff[plotstate.x.value]):
            update_mapping(plotstate, axis="x")
        if check_categorical(dff[plotstate.y.value]):
            update_mapping(plotstate, axis="y")
        assert not check_categorical(dff[plotstate.color.value]), (
            "cannot perform aggregations on categorical data")

        expr = (
            fetch_data(plotstate, dff, axis="x"),
            fetch_data(plotstate, dff, axis="y"),
        )
        expr_c = dff[plotstate.color.value]
        bintype = plotstate.bintype.value

        # get bin widths and props
        # NOTE: ideally this method is delayed; but its not supported to send promises
        edges = [[], []]
        shape = [plotstate.nbins.value, plotstate.nbins.value]
        widths = [1, 1]
        limits = [None, None]
        for i in range(2):
            col = (plotstate.x.value, plotstate.y.value)[i]
            if check_categorical(dff[col]):
                edges[i] = expr[i].unique(array_type="numpy")
                shape[i] = len(edges[i])
                limits[i] = [0, expr[i].nunique()]
                widths[i] = 1
            else:
                try:
                    limit = expr[i].minmax()
                except Exception:  # stride bug catch
                    limit = [expr[i].min()[()], expr[i].max()[()]]
                edges[i] = dff.bin_centers(
                    expression=expr[i],
                    limits=limit,
                    shape=plotstate.nbins.value,
                )
                limits[i] = limit
                shape[i] = plotstate.nbins.value
                widths[i] = (limit[1] - limit[0]) / shape[i]

        # pull the aggregation function pointer and call it with our kwargs
        if bintype == "median":
            aggFunc = getattr(dff, "median_approx")  # median under diff name
        else:
            aggFunc = getattr(dff, bintype)
        color = aggFunc(
            expression=expr_c if bintype != "count" else None,
            binby=expr,
            limits=limits,
            shape=shape,
            delay=True,
        )

        # execute!
        dff.execute()
        color = color.get()

        # convert because it breaks
        if bintype == "count":
            color = color.astype("float")
            color[color == 0] = np.nan
        color[np.abs(color) == np.inf] = np.nan

        # scale if needed
        if plotstate.logcolor.value:
            color = np.log10(color)  # only take log if count
        assert not np.all(np.isnan(color)), "all nan"

        return color, edges[0], edges[1], widths
