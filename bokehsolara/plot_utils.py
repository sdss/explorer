"""Utility functions for generating plot objects and calculations"""

from typing import Optional

from bokeh.models.grids import Grid
from bokeh.models.plots import Plot
from bokeh.models.ranges import DataRange1d
import numpy as np
import vaex as vx
from bokeh.models.scales import LinearScale, LogScale
from bokeh.models.tools import (
    BoxSelectTool,
    BoxZoomTool,
    LassoSelectTool,
    WheelZoomTool,
    HoverTool,
    ExamineTool,
    PanTool,
    ResetTool,
)
from bokeh.models.mappers import (
    LinearColorMapper,
    LogColorMapper,
    CategoricalColorMapper,
)
from bokeh.models.formatters import (
    CustomJSTickFormatter, )
from bokeh.models import CustomJS, ColorBar
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.models.axes import LinearAxis
from bokeh.model import Model

from util import check_categorical

DEV = True  # TODO: switch to read envvar


def add_all_tools(p: Plot, tooltips: Optional[str] = None) -> list[Model]:
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
    tools = [pan, boxzoom, box_select, lasoo, hover, wz, reset]
    if DEV:
        tools.append(ExamineTool())  # debugging tool
    p.add_tools(*tools)
    p.toolbar.active_scroll = wz  # sets scroll wheelzoom
    p.toolbar.autohide = True  # hide when not hovered

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
        palette=plotstate.colorscale.value,
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
        height=
        360,  # NOTE: if you change default viewcard height, this must also change
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

    # add extra ranges
    # NOTE: categorical swaps aren't supported, so we do server-side mapping
    p.extra_x_scales = {
        "lin": LinearScale(),
        "log": LogScale(),
    }
    p.extra_y_scales = {
        "lin": LinearScale(),
        "log": LogScale(),
    }
    p.extra_x_ranges = {
        "lin": DataRange1d(),
        "log": DataRange1d(),
    }
    p.extra_y_ranges = {
        "lin": DataRange1d(),
        "log": DataRange1d(),
    }

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


def generate_datamap(expr: vx.Expression) -> dict[str | bool, int]:
    """Generates a mapping for categorical data"""
    n: int = expr.nunique()
    factors: list[str | bool] = expr.unique()
    return {k: v for (k, v) in zip(factors, range(n))}
