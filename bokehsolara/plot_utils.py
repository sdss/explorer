"""Utility functions for generating plot objects and calculations"""

from typing import Optional, Callable, Any

from bokeh.models.grids import Grid
from bokeh.models.plots import Plot
from bokeh.models.ranges import DataRange1d
from bokeh.plotting import ColumnDataSource
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
    TapTool,
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
from state import PlotState

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


from bokeh.transform import factor_cmap, linear_cmap, log_cmap


def generate_color_mapper_bar(plotstate:PlotState, z: vx.Expression):
    """Get fill_color dataspec, color mapper, and colorbar for colorbar plots

    Arguments
    :plotstate: PlotState -- plot variables
    :z: vx.Expression -- the pre-computed z expression for aggregated data
            some cases will point to unfiltered dataframe (by design) for 
    """

    pass in one of two things
    col = plotstate.color.value
    '''pass in teff'''

    # use correct bokeh function in each case
    if check_categorical(plotstate.color.value):
        fill_color = factor_cmap("z",
                                 palette=plotstate.colorscale.value,
                                 factors=df[col].unique())
    elif plotstate.colorlog.value():
        if getattr(plotstate,'bintype', 'count') != 'count':
            # if it doesn't exist, we have to take the MAXIMA of this column
            expr = df[df[col] > 0][col]
        fill_color = log_cmap("z",
                              palette=plotstate.colorscale.value,
                              low=expr.min()[()],
                              high=expr.max())[()],)
    else:
        fill_color = linear_cmap("z",
                                 palette=plotstate.colorscale.value,
                                 low=z.min()[()],
                                 high=z.max())[()],)

    cb = ColorBar(
        color_mapper=fill_color["transform"],  # dataspec['transform']
        location=(5, 6),
        title=plotstate.color.value,
    )
    return fill_color, cb


def generate_label(plotstate, axis: str = "x") -> str:
    """Generates an axis label."""
    assert axis in ("x", "y", "color")
    col = getattr(plotstate, axis).value
    log = getattr(plotstate,
                  "colorlog" if axis == "color" else f"log{axis}").value
    cond = log and not check_categorical(col)
    bintype = getattr(plotstate, "bintype") if axis == "color" else ""
    if bintype == "count":
        # no col data if just counting
        col = ""
    # very long oneliner
    return f"{'log(' if cond else ''}{bintype}{'(' if bintype != 'count' else ''}{col}{')' if bintype != 'count' else ''}{')' if cond else ''}"


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


def add_callbacks(
    plotstate: PlotState,
    dff: vx.DataFrame,
    p: Plot,
    source: ColumnDataSource,
    set_filter: Optional[Callable[[Any], Any]] = None,
) -> None:
    """
    Adds various callbacks, for filtering, context menu, and
    """
    # grab via names set in generate_plot
    items = [
        p.select(name="menu-propogate")[0],
        p.select(name="menu-table")[0],
        p.select(name="menu-clear")[0],
    ]

    # selection callback to disable/enable these items
    def on_select(attr, old, new):
        for item in items:
            if len(new) == 0:
                # disable button
                item.update(disabled=True)
            else:
                item.update(disabled=False)

    source.selected.on_change("indices", on_select)

    # selection callback to update the filter object
    if set_filter is not None:  # TODO: remove this line make non optional

        def propogate_select_to_filter(attr, old, new):
            if len(new) > 0:
                pass

        source.selected.on_change("indices", propogate_select_to_filter)

    # add reset range event
    def on_reset(event):
        """Range resets"""
        newx = calculate_range(plotstate, dff, "x")
        newy = calculate_range(plotstate, dff, "y")
        with p.hold(render=True):
            p.x_range.update(start=newx[0], end=newx[1])
            p.y_range.update(start=newy[0], end=newy[1])

    p.on_event("reset", on_reset)

    # zora jump
    if (plotstate.plottype == "scatter") or (plotstate.plottype == "skyplot"):
        tapcb = CustomJS(
            args=dict(source=source),
            code="""
            window.open(`https://data.sdss.org/zora/target/${source.data.sdss_id[source.inspected.indices[0]]}`, '_blank').focus();
            """,
        )
        tap = TapTool(
            behavior="inspect",
            callback=tapcb,
            gesture="doubletap",
            visible=False,  # hidden
        )
        p.add_tools(tap)


def generate_tooltips(plotstate: PlotState) -> str:
    if plotstate.plottype == "scatter":
        return (f"""
        <div>
        {plotstate.x.value}: $snap_x
        {plotstate.y.value}: $snap_y
        {plotstate.color.value}: @z
        sdss_id: @sdss_id
        </div>\n""" + """
        <style>
        div.bk-tooltip-content > div > div:not(:first-child) {
            display:none !important;
        } 
        </style>
        """)
    elif plotstate.plottype == "heatmap":
        return (f"""
        <div>
        {plotstate.x.value}: $snap_x
        {plotstate.y.value}: $snap_y
        {plotstate.color.value}: @z
        </div>\n""" + """
        <style>
        div.bk-tooltip-content > div > div:not(:first-child) {
            display:none !important;
        } 
        </style>
        """)
