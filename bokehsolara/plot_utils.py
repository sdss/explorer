import os
from typing import Callable, Optional, cast

from bokeh.models.grids import Grid
from bokeh.models.plots import Plot
from bokeh.models.ranges import DataRange1d, FactorRange
from bokeh.models.tools import WheelZoomTool
import ipywidgets as widgets
import numpy as np
import reacton as r
import reacton.ipyvuetify as rv
import solara as sl
import traitlets as t
import vaex as vx
import xarray
from bokeh.io import output_notebook, curdoc, push_notebook
from bokeh.events import Reset
from bokeh.models.scales import LinearScale, LogScale, CategoricalScale
from bokeh.models import (
    BoxSelectTool,
    BoxZoomTool,
    LassoSelectTool,
    ColorBar,
    HoverTool,
    Scatter,
    ExamineTool,
    TapTool,
    PanTool,
    ResetTool,
)
from bokeh.models.mappers import (
    LinearColorMapper,
    LogColorMapper,
    CategoricalColorMapper,
)
from bokeh.models.formatters import (
    CustomJSTickFormatter,
    LogTickFormatter,
    BasicTickFormatter,
)
from bokeh.models import CustomJS, OpenURL
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from bokeh.models.axes import CategoricalAxis, LogAxis, LinearAxis
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu
from bokeh.models.axes import Axis

from util import check_categorical


def add_all_tools(p: Plot, tooltips: Optional[str] = None):
    """Adds all basic tools, modifies plot's toolbar."""
    # create hovertool
    hover = HoverTool(
        tooltips=tooltips,
        visible=False,
    )

    # generate other tools
    pan = PanTool()
    boxzoom = BoxZoomTool()
    wz = WheelZoomTool()
    box_select = BoxSelectTool()
    lasoo = LassoSelectTool()
    reset = ResetTool()
    examine = ExamineTool()
    tools = [pan, boxzoom, box_select, lasoo, examine, hover, wz, reset]
    p.add_tools(*tools)
    p.toolbar.active_scroll = wz
    p.toolbar.autohide = True

    return tools


def generate_axes(plotstate, p: Plot) -> None:
    """Generates axes and corresponding grids for plots, modifies object inplace."""
    xaxis = LinearAxis(axis_label=generate_label(plotstate, "x"))
    yaxis = LinearAxis(axis_label=generate_label(plotstate, "y"))
    grid_x = Grid(dimension=0, ticker=xaxis.ticker, visible=True)
    grid_y = Grid(dimension=1, ticker=yaxis.ticker, visible=True)
    p.add_layout(xaxis, "below")
    p.add_layout(yaxis, "left")
    p.add_layout(grid_x, "center")
    p.add_layout(grid_y, "center")


def generate_color_mapper_bar(plotstate, z):
    """Get color mapper and colorbar for colorbar plots"""
    if check_categorical(plotstate.color.value):
        mpr = CategoricalColorMapper
        mpr_kwargs = dict()  # TODO: catagorical mapper
    else:
        mpr_kwargs = dict(
            low=z.min(),
            high=z.max(),
        )
        if plotstate.colorlog.value is not None:
            mpr = LogColorMapper
        else:
            mpr = LinearColorMapper
    mapper = mpr(
        palette=plotstate.colormap.value,
        **mpr_kwargs,
    )
    cb = ColorBar(color_mapper=mapper,
                  location=(5, 6),
                  title=plotstate.color.value)
    return mapper, cb


def generate_label(plotstate, axis: str = "x") -> str:
    """Generates an axis label."""
    col = getattr(plotstate, axis).value
    log = getattr(plotstate, f"log{axis}").value
    cond = log and not check_categorical(col)
    return f"{'log(' if cond else ''}{col}{')' if cond else ''}"


def generate_plot(plotstate):
    """Generates basic plot object with context menu, with object bindings"""
    # create menu
    menu = BokehMenu()
    menu.styles = {"color": "black", "font-size": "16px"}

    # generate main Plot model
    p = Plot(
        context_menu=menu,
        toolbar_location="above",
        # height_policy='max', # NOTE: doesn't work
        width_policy="max",
        reset_policy=
        "event_only",  # NOTE: we handle resets ourselves bc changing scales crashes it
        output_backend=
        "webgl",  # for performance, will fallback to HTML5 if unsupported
        lod_factor=20000,
        lod_interval=300,
        lod_threshold=1000,
        lod_timeout=10000,
    )
    name = "menu-propogate"
    items = [
        ActionItem(label="View table of selected targets",
                   disabled=True,
                   name="menu-table"),
        ActionItem(
            label="Propagate selection to new subset",
            disabled=True,
            name="menu-propogate",
        ),
        ActionItem(label="Clear selection", disabled=True, name="menu-clear"),
        ActionItem(
            label="Reset plot",
            action=CustomJS(args=dict(p=p), code="""p.reset.emit()"""),
        ),
    ]
    menu.update(items=items)

    return p, menu


def calculate_range(plotstate, df, axis: str = "x") -> tuple[float, float]:
    """Fetches a new reset-like start/end value based on the flip, log, and column"""
    # bug checking and now get actual stuff
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"
    col = plotstate.x.value if axis == "x" else plotstate.y.value
    flip = plotstate.flipx.value if axis == "x" else plotstate.flipy.value
    log = plotstate.logx.value if axis == "x" else plotstate.logy.value

    expr = df[col]
    if check_categorical(expr):
        limits = (0, expr.nunique() - 1)
    else:
        if log:  # limit to > 0 for log mapping
            expr = np.log10(df[df[col] > 0]
                            [col])  # TODO: may cause assertion error crashes
        try:
            limits = expr.minmax()
        except RuntimeError:
            # TODO: logger debug stride bug
            limits = (expr.min()[()], expr.max()[()])

    # bokeh uses 10% of range as padding by default
    datarange = abs(limits[1] - limits[0])
    pad = datarange / 20
    start = limits[0] - pad
    end = limits[1] + pad
    if log:
        start = 10**start
        end = 10**end

    if not flip:
        return start, end
    else:
        return end, start


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
        colData = dff[col].values
    return colData


def generate_datamap(expr: vx.Expression) -> dict[str | bool, int]:
    """Generates a mapping for categorical data"""
    n: int = expr.nunique()
    factors: list[str | bool] = expr.unique()
    return {k: v for (k, v) in zip(factors, range(n))}


def generate_categorical_tick_formatter(
    mapping: dict[str | bool, int], ) -> CustomJSTickFormatter:
    """
    Generates a categorical tick formatter

    """
    reverseMapping = {v: k for k, v in mapping.items()}
    cjs = """
    var mapper = new Object(mapping);
    return mapper.get(tick) || ""
    """
    return CustomJSTickFormatter(args=dict(mapping=reverseMapping), code=cjs)
