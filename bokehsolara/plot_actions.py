"""Plot specific actions that are used in effects"""

import vaex as vx
import xarray
from bokeh.models.formatters import (
    LogTickFormatter,
    BasicTickFormatter,
)

from util import check_categorical
from state import PlotState
from plot_utils import (
    calculate_range,
    generate_label,
    generate_datamap,
    generate_categorical_tick_formatter,
)


def update_axis(
    plotstate,
    fig_model,
    dff,
    axis: str = "x",
):
    """Direct and complete axis update."""
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


def update_coloraxis(
    plotstate,
    fig_model,
    dff,
):
    """Direct and complete axis update."""
    # get all attributes of plotstate + fig_model
    col = getattr(plotstate, "color").value  # column name
    log = getattr(plotstate, "colorlog").value  # column name
    if (plotstate.plottype == 'heatmap')
        color = aggregate_data(plotstate)[0]
    else:
        color = fetch_data(plotstate, dff, axis=axis)

    
    with fig_model.hold(render=True):
        fig_model.renderers[0].data_source.data[
            'z'] = colData.values  # set data
        
        update_label(plotstate, fig_model, axis=axis) # update colorbar label


def reset_range(plotstate, fig_model, dff, axis: str = "x"):
    """Resets given axis range on a figure model."""
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    datarange = getattr(fig_model, f"{axis}_range")
    # NOTE: flip/log is automatically by the calculation function
    newrange = calculate_range(plotstate, dff, axis=axis)
    datarange.update(start=newrange[0], end=newrange[1])


def update_label(plotstate, fig_model, axis: str = "x") -> None:
    assert axis in ("x", "y",'color'), f"expected axis x or y but got {axis}"
    # gangsta one liner
    loc = ("below" if axis == "x" else "left") if axis != 'color' else 'right'
    ax = getattr(fig_model, loc)[0]
    setattr(ax,ax,'title' if axis == 'color' else 'axis_label',generate_label(plotstate, axis=axis))


def update_mapping(plotstate, axis: str = "x") -> None:
    """Updates the categorical datamapping for the given axis"""
    from state import df  # WARNING: this df must be from SubsetState.subsets later

    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    mapping = generate_datamap(df[col])
    setattr(plotstate, f"{axis}mapping", mapping)  # categorical datamap
    return


def update_color_mapping(plotstate, fig_model, axis):
    """Recreates a figure model and adds it entirely"""


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


def fetch_data(plotstate, dff, axis: str = "x") -> vx.Expression:
    """Helper function to get data and apply mappings if necessary"""
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    if check_categorical(col):
        mapping = getattr(plotstate, f"{axis}mapping")  # categorical datamap
        colData = dff[col].map(mapping)
    else:
        colData = dff[col]
    return colData


def aggregate_data(dff:vx.DataFrame, plotstate: PlotState):
    """
    Create aggregated data expressions for heatmap and histogram

    Arguments
    :dff: filtered dataframe

    """
    # check validity; O(1) because set
    if plotstate.bintype.value not in plotstate.Lookup['bintypes']:
        raise ValueError("no assigned bintype for aggregated")

    # TODO: histogram logic
    # TODO: categorical datum for both heat/hist
    expr = (dff[plotstate.x.value], dff[plotstate.y.value])
    expr_c = dff[plotstate.color.value]
    bintype = plotstate.bintype.value
    df.bin_centers(
        expression=expr[1],
        limits=limits[1],
        shape=plotstate.nbins.value,
    )

    # try and except for stride != 1 bug
    try:
        limits = [
            dff.minmax(plotstate.x.value),
            dff.minmax(plotstate.y.value),
        ]
    except:
        # NOTE: empty tuple acts as index for the 0th of 0D array
        limits = [
            [
                dff.min(plotstate.x.value)[()],
                dff.max(plotstate.x.value)[()],
            ],
            [
                dff.min(plotstate.y.value)[()],
                dff.max(plotstate.y.value)[()],
            ],
        ]


    # pre-compile kwargs to detach array_type if not supported
    kwargs = dict(
            expression=expr_c if bintype != 'count' else None,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            delay=True,
            )

    # pull the aggregation function pointer and call it with our kwargs
    aggFunc = getattr(dff,bintype)
    z = aggFunc(**kwargs)

    dff.execute()
    z = z.get()

    # get coordinate bin centers
    x_edges = dff
    y_edges = z.coords[plotstate.x.value].values

    return z, x_edges, y_edges, limits
