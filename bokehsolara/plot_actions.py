"""Plot specific actions that are used in effects"""

import vaex as vx
from bokeh.models.formatters import (
    LogTickFormatter,
    BasicTickFormatter,
)

from util import check_categorical
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


def reset_range(plotstate, fig_model, dff, axis: str = "x"):
    """Resets given axis range on a figure model."""
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    datarange = getattr(fig_model, f"{axis}_range")
    # NOTE: flip/log is automatically by the calculation function
    newrange = calculate_range(plotstate, dff, axis=axis)
    datarange.update(start=newrange[0], end=newrange[1])


def update_label(plotstate, fig_model, axis: str = "x"):
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    ax = getattr(fig_model, "below" if axis == "x" else "left")[0]
    ax.axis_label = generate_label(plotstate, axis=axis)


def update_mapping(plotstate, axis: str = "x") -> None:
    """Updates the categorical datamapping for the given axis"""
    from state import df  # WARNING: this df must be from SubsetState.subsets later

    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = getattr(plotstate, axis).value  # column name

    mapping = generate_datamap(df[col])
    setattr(plotstate, f"{axis}mapping", mapping)  # categorical datamap
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
