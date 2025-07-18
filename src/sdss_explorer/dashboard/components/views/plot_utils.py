"""Utility functions for generating plot objects and calculations"""

import json
import logging
from typing import Optional, Callable

import numpy as np
import solara as sl
import vaex as vx

from bokeh.models.grids import Grid
from bokeh.models.plots import Plot
from bokeh.models.ranges import DataRange1d
from bokeh.plotting import ColumnDataSource
from bokeh.models.scales import LinearScale, LogScale
from bokeh.models.tools import (
    BoxSelectTool,
    BoxZoomTool,
    CustomJSHover,
    LassoSelectTool,
    SaveTool,
    WheelZoomTool,
    HoverTool,
    ExamineTool,
    PanTool,
    ResetTool,
    TapTool,
)
from bokeh.models.mappers import (
    LinearColorMapper, )
from bokeh.models.formatters import (
    CustomJSTickFormatter, )
from bokeh.models import CustomJS, ColorBar, FixedTicker
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.models.axes import LinearAxis
from bokeh.model import Model

from ...dataclass import PlotState, State, SubsetState, Alert
from ....util.config import settings

DEV = settings.dev

logger = logging.getLogger("dashboard")


def check_categorical(expression: str | vx.Expression) -> bool:
    if isinstance(expression, str):
        expression: vx.Expression = State.df.value[expression]
    return (expression.dtype == "string") | (expression.dtype == "bool")


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
    lasoo = LassoSelectTool(continuous=False)  # only evaluate on LMB.up
    reset = ResetTool()
    save = SaveTool()
    tools = [pan, boxzoom, box_select, lasoo, hover, wz, save, reset]

    if DEV:
        tools.append(
            ExamineTool())  # debugging tool to inspect JS props directly
    p.add_tools(*tools)
    p.toolbar.active_scroll = wz  # sets scroll wheelzoom
    p.toolbar.autohide = True  # hide when not hovered

    return tools


def add_axes(plotstate: PlotState, p: Plot) -> None:
    """Generates axes and corresponding grids for plots, modifies object inplace.

    Args:
        plotstate: plot variables
        p: figure

    """
    xaxis = LinearAxis(axis_label=generate_label(plotstate, "x"))
    yaxis = LinearAxis(axis_label=generate_label(plotstate, "y"))
    grid_x = Grid(dimension=0, ticker=xaxis.ticker, visible=True)
    grid_y = Grid(dimension=1, ticker=yaxis.ticker, visible=True)
    p.add_layout(xaxis, "below")
    p.add_layout(yaxis, "left")
    p.add_layout(grid_x, "center")
    p.add_layout(grid_y, "center")


def generate_plot(range_padding: float = 0.1):
    """Generates basic plot object with context menu, with object bindings."""
    # create menu
    menu = BokehMenu()
    menu.styles = {"color": "black", "font-size": "16px"}

    # generate main Plot model
    # NOTE: if you change default viewcard height, this must also change
    p = Plot(
        name="0",
        context_menu=menu,
        toolbar_location="above",
        height=360,
        height_policy=
        "fixed",  # do what we tell you and don't try to go find bounds
        # height_policy=
        # "fit",  # NOTE: this doesn't work in the Lumino context of the cards
        width_policy="max",
        reset_policy=
        "event_only",  # NOTE: we handle resets ourselves bc changing scales crashes it
        output_backend=
        "webgl",  # for performance, will fallback to HTML5 if unsupported
        lod_factor=20000,
        lod_interval=300,
        lod_threshold=1000,
        lod_timeout=10000,
        x_range=DataRange1d(range_padding=range_padding),
        y_range=DataRange1d(range_padding=range_padding),
    )
    name = "menu-propogate"
    items = [
        ActionItem(label="Clear selection", disabled=True, name="menu-clear"),
        ActionItem(
            label="Reset plot",
            name="reset-view",
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
        "lin": DataRange1d(range_padding=range_padding),
        "log": DataRange1d(range_padding=range_padding),
    }
    p.extra_y_ranges = {
        "lin": DataRange1d(range_padding=range_padding),
        "log": DataRange1d(range_padding=range_padding),
    }

    return p, menu


def add_colorbar(plotstate: PlotState, p: Plot,
                 color_mapper: LinearColorMapper, data) -> None:
    """Adds a colorbar to plot. Used during initialization.

    Args:
        plotstate: plot variables
        p: figure
        color_mapper: color mapper object, generated by `generate_color_mapper`
        data (np.ArrayLike): data column of color, used for initializing limits

    """
    cb = ColorBar(
        color_mapper=color_mapper,  # color_mapper object
        ticker=FixedTicker(
            ticks=calculate_colorbar_ticks(np.nanmin(data), np.nanmax(data))),
        location=(5, 6),
        title=generate_label(plotstate, axis="color"),
    )
    p.add_layout(cb, "right")


def _calculate_color_range(
    plotstate: PlotState,
    dff: Optional[vx.DataFrame] = None,
    color: Optional[np.ndarray] = None,
) -> tuple[float, float]:
    """Calculates low/high for colormapper.

    Args:
        plotstate: plot variables
        dff: filtered dataframe
        color: optional pre-computed aggregation data.
    """
    col = plotstate.color.value

    if dff is None and color is None:
        assert ValueError("no data provided to calculate color with")

    # get correct
    if color is None:
        expr = dff[col]
    else:
        expr = color

    if plotstate.plottype == "heatmap":
        assert color is not None, "expected color handoff but got nothing"
        assert not check_categorical(
            col), "handed categorical data for aggregation"
        bintype = getattr(plotstate, "bintype")
        if (bintype == "count") and not plotstate.logcolor.value:
            low = 0
        else:
            low = np.nanmin(expr)
        high = np.nanmax(expr)
    else:
        assert color is None, f"expected no color handoff but got {color}"
        if check_categorical(col):
            # NOTE: colormapping must be updated before this
            low = 0
            high = len(plotstate.colormapping) - 1
        else:
            if plotstate.logcolor.value:
                expr = np.log10(dff[dff[col] > 0]
                                [col])  # WARNING: may throw AssertionError
            low = expr.min()[()]
            high = expr.max()[()]
    return low, high


def generate_color_mapper(
    plotstate: PlotState,
    dff: Optional[vx.DataFrame] = None,
    color: Optional[np.ndarray] = None,
) -> LinearColorMapper:
    """Create a colormapper.

    Args:
        plotstate: plot variables
        color: pre-computed aggregated data array.
    """
    low, high = _calculate_color_range(plotstate, dff=dff, color=color)

    return LinearColorMapper(
        palette=plotstate.Lookup["colorscales"][plotstate.colorscale.value],
        low=low,
        high=high,
    )


def generate_label(plotstate: PlotState, axis: str = "x") -> str:
    """Generates an axis label.

    Args:
        plotstate: plot variables
        axis: which axis to generate a label for. Any of ('x', 'y', or 'color')

    Returns:
        A formatted, pretty axis label
    """
    assert axis in ("x", "y", "color")
    if (plotstate.plottype == "histogram") and (axis == "y"):
        col = getattr(plotstate, "x").value
    else:
        col = getattr(plotstate, axis).value
    log = getattr(plotstate, f"log{axis}").value
    cond = log
    if plotstate.plottype != "histogram":
        cond = cond and not check_categorical(col)
    if (axis == "color") and (plotstate.plottype == "heatmap"):
        bintype = getattr(plotstate, "bintype").value
        bincond = (bintype != "count") and (bintype != "")
        if bintype == "count":
            # no col data if just counting
            col = ""
    elif (plotstate.plottype == "histogram") and (axis == "y"):
        bintype = "count"
        bincond = True
    else:
        bintype = ""
        bincond = False

    # very long oneliner
    return f"{'log(' if cond else ''}{bintype}{'(' if bincond else ''}{col}{')' if bincond else ''}{')' if cond else ''}"


def add_callbacks(
    plotstate: PlotState,
    dff: vx.DataFrame,
    p: Plot,
    source: ColumnDataSource,
    set_filter: Callable,
) -> None:
    """
    Adds various callbacks, for filtering, context menu, and resets.

    Args:
        plotstate: plot variables
        dff: filtered dataframe
        p: figure
        source: data source object
        set_filter: filter setter function
    """
    # add filter reset on 'clear selection' button
    filterResetCJS = CustomJS(
        args=dict(source=source),
        code="""
             source.selected.indices = [];
             source.selected.indices.change.emit();
             """,
    )

    item = p.select(name="menu-clear")[0]
    item.action = filterResetCJS

    # selection callback to disable/enable these items
    def on_select(attr, old, new):
        if len(new) == 0:
            # disable button
            item.update(disabled=True)
        else:
            item.update(disabled=False)

    source.selected.on_change("indices", on_select)

    # add reset range event
    def on_reset(event):
        """Range resets"""
        name = p.name
        p.update(name=str(int(name) + 1))

    p.on_event("reset", on_reset)

    # check for zora base cookie, default to public site
    zbase = sl.lab.cookies.value.get('sdss_zora_base', 'dr19.sdss.org')
    base = f'http://{zbase}' if "localhost" in zbase else f'https://{zbase}/zora'

    # zora jump
    if (plotstate.plottype == "scatter") or (plotstate.plottype == "skyplot"):
        # TODO: chnage to envvar
        tapcb = CustomJS(
            args=dict(source=source),
            code=f"""
            window.open(`{base}/target/${{source.data.sdss_id[source.inspected.indices[0]]}}`, '_blank').focus();
            """,
        )
        tap = TapTool(
            behavior="inspect",
            callback=tapcb,
            gesture="doubletap",
            visible=False,  # hidden
        )
        p.add_tools(tap)


def calculate_range(plotstate: PlotState,
                    dff: vx.DataFrame,
                    axis: str = "x") -> tuple[float, float]:
    """
    Fetches a new reset-like start/end value based on the flip, log, and column.

    Note:
        This already accounts for log scaling and flipping. One simply just has to set start/end props on the range.

    Args:
        plotstate: plot variables
        dff: filtered dataframe
        axis: the axis to perform on ('x' or 'y')

    Returns:
        tuple for start/end props of range.
    """
    df = SubsetState.subsets.value[plotstate.subset.value].df

    # bug checking
    assert axis in ("x", "y"), f"expected axis x or y but got {axis}"

    # fetch
    if (plotstate.plottype == "histogram") and (axis == "y"):
        raise Exception("shouldnt be here")
    col = plotstate.x.value if axis == "x" else plotstate.y.value
    flip = plotstate.flipx.value if axis == "x" else plotstate.flipy.value
    log = plotstate.logx.value if axis == "x" else plotstate.logy.value

    expr = dff[col]
    if check_categorical(expr):
        expr = df[col]
        limits = (0, expr.nunique() - 1)
    else:
        if log:  # limit to > 0 for log mapping
            expr = np.log10(dff[dff[col] > 0]
                            [col])  # TODO: may cause assertion error crashes
        try:
            limits = expr.minmax()
        except RuntimeError:
            logger.debug("dodging stride bug")
            limits = (expr.min()[()], expr.max()[()])

    datarange = abs(limits[1] - limits[0])

    # padding logic
    if (plotstate.plottype == "histogram") and check_categorical(col):
        pad = 1.2
    elif plotstate.plottype == "heatmap":
        if check_categorical(dff[col]):
            pad = 0.5
        else:
            pad = 0
    else:
        # bokeh uses 10% of range as padding by default
        pad = datarange / 20

    start = limits[0]
    end = limits[1]
    start = start - pad
    end = end + pad
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
    Generates a categorical tick formatter.
    Works by reversing the mapping and compiling a new JS code.

    Args:
        mapping: Pre-generated mapping of categories to integers.

    Returns:
        formatter: new formatter to perform mapping
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


def generate_categorical_hover_formatter(plotstate: PlotState,
                                         axis: str = "x") -> CustomJSHover:
    """Generates tooltips for a hovertool based on current plotstate.

    Args:
        plotstate: plot variables
        axis: axis to generate for, any of 'x','y', or 'color'.

    Returns:
        CustomJSHover: a Bokeh CustomJSHover to convert categorical data into actual data.
    """
    assert axis in ("x", "y", "color"), (
        f'expected axis to be "x","y", or "color" but got {axis}')
    if (plotstate.plottype == "histogram") and (axis == "y"):
        # early exit
        return CustomJSHover(code="return value.toFixed(4);")
    else:
        col = getattr(plotstate, axis).value
    mapping = getattr(plotstate, f"{axis}mapping")
    if check_categorical(col):
        cjs = f"return ({json.dumps({v: k for k, v in mapping.items()})})[Math.floor(value)];"
    else:
        cjs = "return value.toFixed(4);"

    return CustomJSHover(code=cjs)


def generate_tooltips(plotstate: PlotState) -> str:
    """Generates tooltips for a hovertool based on current plotstate.

    Args:
        plotstate: plot variables
    """

    def generate_row(label, value):
        return f"""
            <div style="display: table-row">
                <div style="display: table-cell; color: #0D47A1; text-align: right;">
                    {label}:
                </div>
                <div style="display: table-cell;">
                    {value}
                </div>
            </div>
        """

    # define the labels and corresponding values based on plottype
    if plotstate.plottype == "histogram":
        labels_values = [
            (generate_label(plotstate, axis="x"), "@centers{0}"),
            (generate_label(plotstate, axis="y"), "@y{0}"),
        ]
    else:
        labels_values = [
            (generate_label(plotstate, axis="x"), "$snap_x{0}"),
            (generate_label(plotstate, axis="y"), "$snap_y{0}"),
            (generate_label(plotstate, axis="color"), "@color{0}"),
        ]
        if plotstate.plottype == "scatter":
            labels_values.append(("sdss_id", "@sdss_id"))

    # generate the rows dynamically
    rows = "".join(
        generate_row(label, value) for label, value in labels_values)

    # construct the full HTML structure
    return (
        f"""
    <div>
        <div style="display: table; border-spacing: 2px;">
            {rows}
        </div>
    </div>""" + """
    <style>
        div.bk-tooltip-content > div > div:not(:first-child) {
            display:none !important;
        }
    </style>"""
    )  # this is a hack to stop multiple point's tips from displaying at once


def calculate_colorbar_ticks(low, high) -> list[float]:
    """Manually calculates colorbar ticks to bypas low-level Bokeh object replacement locks."""

    def get_interval(data_low, data_high, desired_n_ticks):
        """Helper to get ticks interval. Translated from AdaptiveTicker in BokehJS."""
        data_range = data_high - data_low
        ideal_interval = (data_high - data_low) / desired_n_ticks

        def extended_mantissas():
            mantissas = [1, 2, 5]
            prefix_mantissa = mantissas[-1]
            suffix_mantissa = mantissas[0]
            return [prefix_mantissa] + mantissas + [suffix_mantissa]

        def clamp(value, min_val, max_val):
            return max(min_val, min(value, max_val))

        interval_exponent = np.floor(np.log10(ideal_interval))
        ideal_magnitude = 10**interval_exponent

        candidate_mantissas = extended_mantissas()
        errors = [
            abs(desired_n_ticks - (data_range / (mantissa * ideal_magnitude)))
            for mantissa in candidate_mantissas
        ]

        best_mantissa = candidate_mantissas[np.argmin(errors)]
        interval = best_mantissa * ideal_magnitude
        return clamp(interval, 0, float("inf"))

    try:
        assert low != high
        interval = get_interval(low, high, 6)
        return np.arange(round(low / interval) * interval, high,
                         interval).tolist()
    except Exception as e:
        # dummy data on failure, will show nothing on colorbar
        return np.arange(0, 3 + 0.5, 0.5)
