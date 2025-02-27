"""Plot specific actions that are used in effects"""

from bokeh.models.tools import HoverTool
from typing import Optional, Any
import vaex as vx
from numpy import ndarray
from bokeh.models import Plot
from bokeh.models.formatters import (
    LogTickFormatter,
    BasicTickFormatter,
)

from util import check_categorical
from state import PlotState
from plot_utils import (
    calculate_range,
    generate_color_mapper,
    generate_label,
    generate_datamap,
    generate_categorical_tick_formatter,
    generate_tooltips,
)


def update_tooltips(plotstate: PlotState, fig_model: Plot) -> None:
    """Updates tooltips on toolbar's HoverTool"""
    for tool in fig_model.toolbar.tools:
        if isinstance(tool, HoverTool):
            tool.tooltips = generate_tooltips(plotstate)


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
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name
    if check_categorical(col):
        # update before datafetch
        update_mapping(plotstate, axis=axis)
    colData = fetch_data(plotstate, dff, axis=axis)
    with fig_model.hold(render=True):
        change_formatter(plotstate, fig_model,
                         axis=axis)  # change to cat if needed
        fig_model.renderers[0].data_source.data[
            axis] = colData.values  # set data
        update_label(plotstate, fig_model, axis=axis)
        reset_range(plotstate, fig_model, dff, axis=axis)
        update_tooltips(plotstate, fig_model)


def update_coloraxis(
    plotstate: PlotState,
    fig_model: Plot,
    dff: vx.DataFrame,
    update_data: bool = True,
) -> None:
    """Direct and complete coloraxis update.

    Args:
        plotstate: plot variables
        fig_model: figure object
        dff: filtered dataframe
    """
    # get all attributes of plotstate + fig_model
    if update_data:
        if plotstate.plottype == "heatmap":
            color = aggregate_data(plotstate, dff)[0].flatten()
            colordata = color  # no values prop for ndarray
        else:
            color = dff[plotstate.color.value]
            colordata = color.values

    with fig_model.hold(render=True):
        if update_data:
            fig_model.renderers[0].data_source.data[
                "z"] = colordata  # set data
            update_color_mapper(plotstate, fig_model,
                                z=color)  # replace mapping
        update_label(plotstate, fig_model,
                     axis="color")  # update colorbar label
        update_tooltips(plotstate, fig_model)


def reset_range(plotstate: PlotState, fig_model: Plot, dff, axis: str = "x"):
    """Resets given axis range on a figure model.

    Args:
        plotstate: plot variables
        fig_model: figure object
        axis: axis to update for. 'x', 'y', or 'color'.

    """
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    datarange = getattr(fig_model, f"{axis}_range")
    # NOTE: flip/log is automatically by the calculation function
    newrange = calculate_range(plotstate, dff, axis=axis)
    datarange.update(start=newrange[0], end=newrange[1])


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
        axis: axis to perform update on. any of 'x' or 'y'.

    """
    from state import df  # WARNING: this df must be from SubsetState.subsets later

    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    mapping = generate_datamap(df[col])
    setattr(plotstate, f"{axis}mapping", mapping)  # categorical datamap
    return


def update_color_mapper(
    plotstate: PlotState,
    fig_model: Plot,
    z: Optional[vx.Expression | ndarray] = None,
) -> None:
    """Recreates a color mapper model and adds it everywhere necessary, from glyph (rendered plot) to colorbar.

    Args:
        plotstate: plot variables
        fig_model: plot object to update
        z: optional pre-computed expression to generate new color mapper against. Parsed down to `generate_color_mapper`.

    """
    fill_color = generate_color_mapper(plotstate, z=z)
    fig_model.renderers[0].glyph.fill_color = fill_color  # set on plot
    fig_model.right[0].color_mapper = fill_color[
        "transform"]  # set on colorbar
    return


def change_formatter(plotstate, fig_model, axis: str = "x") -> None:
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name
    log = getattr(plotstate, f"log{axis}").value  # whether log
    mapping = getattr(plotstate, f"{axis}mapping")  # categorical datamap

    ax = getattr(fig_model,
                 "below" if axis == "x" else "left")[0]  # axis object pointer

    if check_categorical(col):
        ax.formatter = generate_categorical_tick_formatter(mapping)
    else:
        ax.formatter = BasicTickFormatter() if not log else LogTickFormatter()


def fetch_data(plotstate: PlotState,
               dff: vx.DataFrame,
               axis: str = "x") -> vx.Expression:
    """Helper function to get data and apply mappings if necessary

    Args:
        plotstate: plot variables
        fig_model: figure object
        axis: axis to fetch for. either 'x' or 'y'.

    Returns:
        Expression of mapped categorical data or raw expression.

    """
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    if check_categorical(col):
        # NOTE: we always ensure this is altered prior to fetch
        mapping = getattr(plotstate,
                          f"{axis}mapping").value  # categorical datamap
        colData = dff[col].map(mapping)
    else:
        colData = dff[col]
    return colData


def aggregate_data(
        plotstate: PlotState, dff: vx.DataFrame
) -> tuple[ndarray, ndarray, ndarray, list[list[float]]]:
    """
    Create aggregated data expressions for heatmap and histogram

    Args:
        plotstate: plot variables
        dff: filtered dataframe

    Returns:
        z (numpy.ndarray): aggregated data according to `plotstate.bintype`
        x_edges: 1D array of x-axis coordinates
        y_edges: 1D array of x-axis coordinates
        limits: x and y axis limits


    """
    # check validity; O(1) because set
    if plotstate.bintype.value not in plotstate.Lookup["bintypes"]:
        raise ValueError(
            "no assigned bintype for aggregation. bug somewhere in settings.")

    # TODO: histogram logic
    # TODO: categorical datum for heatmap
    # TODO: categorical for hist

    # update mappings if needed
    if check_categorical(dff[plotstate.x.value]):
        update_mapping(plotstate, axis="x")
    if check_categorical(dff[plotstate.y.value]):
        update_mapping(plotstate, axis="y")

    expr = (
        fetch_data(plotstate, dff, axis="x"),
        fetch_data(plotstate, dff, axis="y"),
    )
    expr_c = dff[plotstate.color.value]
    bintype = plotstate.bintype.value

    # try and except for stride != 1 bug
    try:
        limits = [
            expr[0].minmax(),
            expr[1].minmax(),
        ]
    except Exception:
        # NOTE: empty tuple acts as index for the 0th of 0D array
        limits = [
            [
                expr[0].min(),
                expr[0].max(),
            ],
            [
                expr[1].min(),
                expr[1].max(),
            ],
        ]

    # get bin centers
    # NOTE: ideally this method is delayed; but its not supported
    x_edges = dff.bin_centers(
        expression=expr[0],
        limits=limits[0],
        shape=plotstate.nbins.value,
    )
    y_edges = dff.bin_centers(
        expression=expr[1],
        limits=limits[1],
        shape=plotstate.nbins.value,
    )

    # pull the aggregation function pointer and call it with our kwargs
    aggFunc = getattr(dff, bintype)
    z = aggFunc(
        expression=expr_c if bintype != "count" else None,
        binby=expr,
        limits=limits,
        shape=plotstate.nbins.value,
        delay=True,
        array_type="numpy",
    )

    # execute!
    dff.execute()
    z = z.get()

    return z, x_edges, y_edges, limits
