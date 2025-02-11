import os
from typing import Callable, Optional, cast

from bokeh.models.grids import Grid
from bokeh.models.plots import Plot
from bokeh.models.ranges import DataRange1d
from bokeh.models.tools import WheelZoomTool
import ipyvuetify as v
import ipywidgets as widgets
import numpy as np
import reacton as r
import reacton.ipyvuetify as rv
import solara as sl
import ipyvuetify as ipv
import traitlets as t
import vaex as vx
import xarray
from bokeh.io import output_notebook, curdoc, push_notebook
from bokeh.events import DocumentReady, Reset
from bokeh.models.scales import LinearScale, LogScale, CategoricalScale
from bokeh.models import (
    BoxSelectTool,
    ColorBar,
    HoverTool,
    Scatter,
    TapTool,
)
from bokeh.models.mappers import (
    LinearColorMapper,
    LogColorMapper,
    CategoricalColorMapper,
)
from bokeh.models import CustomJS, OpenURL
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from bokeh.models.axes import CategoricalAxis, LogAxis, LinearAxis
from bokeh.themes import Theme
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu

from plot_utils import (
    add_all_tools,
    generate_axes,
    generate_color_mapper_bar,
    generate_plot,
    generate_xlabel,
    generate_ylabel,
)
from state import plotstate, df, GridState
from figurebokeh import FigureBokeh
from util import check_categorical

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,examine"

colormaps = [x for x in colormaps if "256" in x]

index_context = sl.create_context(0)
# https://docs.bokeh.org/en/latest/docs/user_guide/interaction/js_callbacks.html#customjs-for-topics-events

from plot_themes import LIGHTTHEME, DARKTHEME, darkprops, lightprops


def get_data():
    expr = (df[plotstate.x.value], df[plotstate.y.value])
    expr_c = df[plotstate.color.value]
    bintype = plotstate.bintype.value
    try:
        limits = [
            df.minmax(plotstate.x.value),
            df.minmax(plotstate.y.value),
        ]
    except:
        # NOTE: empty tuple acts as index for the 0th of 0D array
        limits = [
            [
                df.min(plotstate.x.value)[()],
                df.max(plotstate.x.value)[()],
            ],
            [
                df.min(plotstate.y.value)[()],
                df.max(plotstate.y.value)[()],
            ],
        ]

    if bintype == "count":
        z = df.count(
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
            delay=True,
        )
    elif bintype == "sum":
        z = df.sum(
            expr_c,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
            delay=True,
        )
    elif bintype == "mean":
        z = df.mean(
            expr_c,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
            delay=True,
        )
    elif bintype == "median":
        z = df.median_approx(
            expr_c,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            delay=True,
        )
    elif bintype == "mode":
        z = df.mode(
            expression=expr_c,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            delay=True,
        )
    elif bintype == "min":
        z = df.min(
            expression=expr_c,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
            delay=True,
        )
    elif bintype == "max":
        z = df.max(
            expression=expr_c,
            binby=expr,
            limits=limits,
            shape=plotstate.nbins.value,
            array_type="xarray",
            delay=True,
        )
    else:
        raise ValueError("no assigned bintype for aggregated")
    df.execute()
    z = z.get()
    if bintype == "median":
        # convert to xarray
        z = xarray.DataArray(
            z,
            coords={
                plotstate.x.value:
                df.bin_centers(
                    expression=expr[0],
                    limits=limits[0],
                    shape=plotstate.nbins.value,
                ),
                plotstate.y.value:
                df.bin_centers(
                    expression=expr[1],
                    limits=limits[1],
                    shape=plotstate.nbins.value,
                ),
            },
        )

    # change 0 to nan for coloring purposes
    if bintype == "count":
        z = z.where(np.abs(z) != 0, np.nan)

    x_edges = z.coords[plotstate.x.value].values
    y_edges = z.coords[plotstate.x.value].values
    return z, x_edges, y_edges, limits


@sl.component()
def HeatmapPlot():
    return sl.Card()

    def create_figure():
        """Creates figure with relevant objects"""
        # obtain data
        z, x_centers, y_centers, limits = get_data()

        # create menu
        menu = BokehMenu(items=[
            ActionItem(
                label="test",  # this isnt visible, how fix?
                action=CustomJS(
                    code=
                    """window.open('https://www.google.com', '_blank').focus()"""
                ),  # bound to reactive of last hovered points
            ),
        ])
        menu.styles = {"color": "black", "font-size": "16px"}

        # generate source object
        source = ColumnDataSource(
            data={
                "x": np.repeat(x_centers, len(y_centers)),
                "y": np.tile(y_centers, len(x_centers)),
                "z": z.values.flatten(),
            })

        # generate main figure
        p = figure(
            x_axis_label=plotstate.x.value,
            y_axis_label=plotstate.y.value,
            tools=TOOLS,
            context_menu=menu,
            toolbar_location="above",
            # height_policy='max',
            width_policy="max",
            active_scroll="wheel_zoom",  # default to scroll wheel for zoom
            output_backend=
            "webgl",  # for performance, will fallback to HTML5 if unsupported
        )

        # setup colormap
        mapper = LinearColorMapper(palette=plotstate.colormap.value,
                                   low=z.min().item(),
                                   high=z.max().item())

        # generate rectangles
        glyph = p.rect(
            x="x",
            y="y",
            width=(limits[0][1] - limits[0][0]) / plotstate.nbins.value * 1.02,
            height=(limits[1][1] - limits[1][0]) / plotstate.nbins.value,
            source=source,
            line_color=None,
            fill_color={
                "field": "z",
                "transform": mapper
            },
        )

        # create hovertool, bound to figure object
        TOOLTIPS = [
            (plotstate.x.value, "$x"),
            (plotstate.y.value, "$y"),
            (plotstate.bintype.value, "@z"),
        ]
        hover = HoverTool(tooltips=TOOLTIPS, renderers=[glyph], visible=False)
        p.add_tools(hover)

        # add selection tools
        box_select = BoxSelectTool(renderers=[glyph])
        p.add_tools(box_select)

        return p, source, mapper, menu, (hover, box_select)

    p, source, mapper, menu, tools = sl.use_memo(create_figure,
                                                 dependencies=[])

    # source on selection effect
    def on_select(attr, old, new):
        print(attr)
        print(old)
        print(new)
        print(source.selected.indices)

    source.selected.on_change("indices", on_select)

    def add_effects(pfig):

        def change_heatmap_data():
            if pfig is not None:
                fig_element: BokehModel = sl.get_widget(pfig)
                z, x_centers, y_centers, limits = get_data()

                # directly update data
                source.data = {
                    "x": np.repeat(x_centers, len(y_centers)),
                    "y": np.tile(y_centers, len(x_centers)),
                    "z": z.values.flatten(),
                }

                # update colorbar
                mapper.low = z.min().item()
                mapper.high = z.max().item()

                if False:
                    newfig = create_figure()  # recreate figure
                    fig_element.update_from_model(
                        newfig)  # replace the main model
                return

        def change_xy_data():
            if pfig is not None:
                fig_element: BokehModel = sl.get_widget(pfig)
                z, x_centers, y_centers, limits = get_data()

                # directly update data
                source.data = {
                    "x": np.repeat(x_centers, len(y_centers)),
                    "y": np.tile(y_centers, len(x_centers)),
                    "z": z.values.flatten(),
                }

                # update x/y labels

                # update colorbar
                mapper.low = z.min().item()
                mapper.high = z.max().item()
                return

        def change_colormap():
            if pfig is not None:
                mapper.palette = plotstate.colormap.value

        sl.use_effect(change_xy_data,
                      dependencies=[plotstate.x.value, plotstate.y.value])
        sl.use_effect(
            change_heatmap_data,
            dependencies=[
                plotstate.color.value,
                plotstate.bintype.value,
            ],
        )
        sl.use_effect(change_colormap, dependencies=[plotstate.colormap.value])

    pfig = FigureBokeh(p)
    add_effects(pfig)
    return pfig


def ScatterPlot():
    filter, set_filter = sl.use_cross_filter(id(df), name="scatter")
    dark = sl.lab.use_dark_effective()
    counter = sl.use_reactive(0)
    i = sl.use_context(index_context)
    layout, set_layout = sl.use_state({"w": 6, "h": 10, "i": i})

    def update_grid():
        # fetch from gridstate
        for spec in GridState.grid_layout.value:
            if spec["i"] == i:
                set_layout(spec)
                break

    sl.lab.use_task(update_grid, dependencies=[GridState.grid_layout.value])
    if filter:
        dff = df[filter]
    else:
        dff = df

    def generate_tooltips(plotstate):
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

    source = sl.use_memo(
        lambda: ColumnDataSource(
            data={
                "x": dff[plotstate.x.value].values,
                "y": dff[plotstate.y.value].values,
                "z": dff[plotstate.color.value].values,
                "sdss_id": dff["L"].values,  # temp
            }),
        dependencies=[],
    )

    def create_figure():
        """Creates figure with relevant objects"""
        p, menu = generate_plot(plotstate)
        # generate and add axes
        p = generate_axes(plotstate, p)
        p.extra_x_scales = {
            "lin": LinearScale(),
            "log": LogScale(),
            "cat": CategoricalScale(),
        }
        p.extra_y_scales = {
            "lin": LinearScale(),
            "log": LogScale(),
            "cat": CategoricalScale(),
        }

        # generate scatter points
        mapper, cb = generate_color_mapper_bar(
            plotstate, dff[plotstate.color.value].values)
        glyph = Scatter(
            x="x",
            y="y",
            size=8,
            fill_color={
                "field": "z",
                "transform": mapper,
            },
        )

        p.add_glyph(source, glyph)
        p.add_layout(cb, "right")

        # add all tools; custom hoverinfo
        add_all_tools(p, tooltips=generate_tooltips(plotstate))

        # zora jump
        tapcb = CustomJS(
            args=dict(source=source),
            code="""console.log('Tap');
            console.log(source.selected.indices);
            window.open(`https://data.sdss.org/zora/target/${source.data.sdss_id[source.inspected.indices[0]]}`, '_blank').focus();
            """,
        )
        tap = TapTool(
            behavior="inspect",
            callback=tapcb,
            gesture="doubletap",
            visible=False,
        )
        p.add_tools(tap)

        # source on selection effect
        def on_select(attr, old, new):
            item = p.select(name="menu-propogate")[0]
            if len(new) == 0:
                # disable button
                item.update(disabled=True)
            else:
                item.update(disabled=False)

        source.selected.on_change("indices", on_select)

        def on_reset(event):
            print("I HAVE RESET!!!")
            print(event.model)

        p.on_event("reset", on_reset)

        return p, mapper, menu, cb

    p, mapper, menu, cb = sl.use_memo(
        create_figure,
        dependencies=[],
    )

    def add_effects(pfig):

        def update_x():
            # TODO: ensure no catagorical data failure
            # update CDS
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                x = dff[plotstate.x.value].values
                source.data["x"] = x

                # replace grid and axes objects
                p.below[0].axis_label = generate_xlabel(plotstate)

        def update_y():
            # TODO: ensure no catagorical data failure
            # update CDS
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                fig_model: plot = fig_widget._model
                y = dff[plotstate.y.value].values
                source.data["y"] = y
                p.left[0].axis_label = generate_ylabel(plotstate)

        def update_color():
            # TODO: ensure no catagorical data failure
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                fig_model: Plot = fig_widget._model
                fig_model.hold_render = True
                z = dff[plotstate.color.value].values
                z = np.log10(z) if plotstate.colorlog.value else z
                source.data["z"] = z
                mapper.update(low=z.min(), high=z.max())
                fig_model.hold_render = False
                cb.title = plotstate.color.value

        def update_cmap():
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                fig_model: Plot = fig_widget._model
                mapper.palette = plotstate.colormap.value

        def update_flip():
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                fig_model: Plot = fig_widget._model
                # TODO: catagorical support

                # bokeh uses 1/20th of range as padding
                xrange = abs(dff[plotstate.x.value].min()[()] -
                             dff[plotstate.x.value].max()[()])
                xpad = xrange / 20
                yrange = abs(dff[plotstate.y.value].min()[()] -
                             dff[plotstate.y.value].max()[()])
                ypad = yrange / 20

                fig_model.x_range.start = (dff[plotstate.x.value].min()[
                    ()] if not plotstate.flipx.value else dff[
                        plotstate.x.value].max()[()]) - (
                            xpad if not plotstate.flipx.value else -xpad)
                fig_model.x_range.end = (dff[plotstate.x.value].max()[
                    ()] if not plotstate.flipx.value else dff[
                        plotstate.x.value].min()[()]) + (
                            xpad if not plotstate.flipx.value else -xpad)
                fig_model.y_range.start = (dff[plotstate.y.value].min()[()]
                                           if not plotstate.flipy.value else
                                           dff[plotstate.y.value].max()[()])
                fig_model.y_range.end = (dff[plotstate.y.value].max()[()]
                                         if not plotstate.flipy.value else
                                         dff[plotstate.y.value].min()[()])
                fig_model.x_range.flipped = plotstate.flipx.value
                fig_model.y_range.flipped = plotstate.flipy.value

        def update_filter():
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                x = dff[plotstate.x.value].values
                y = dff[plotstate.y.value].values
                source.data = dict(
                    x=np.log10(x) if plotstate.logx.value else x,
                    y=np.log10(y) if plotstate.logy.value else y,
                    z=dff[plotstate.color.value].values,
                    sdss_id=dff["L"].values,
                )

        def update_log():
            fig_widget: BokehModel = sl.get_widget(pfig)
            if isinstance(fig_widget, BokehModel):
                if plotstate.logx.value:
                    p.x_scale = p.extra_x_scales["log"]
                else:
                    p.x_scale = p.extra_x_scales["lin"]
                if plotstate.logy.value:
                    p.y_scale = p.extra_x_scales["log"]
                else:
                    p.y_scale = p.extra_x_scales["lin"]

        sl.use_effect(update_filter, dependencies=[filter])
        sl.use_effect(update_x, dependencies=[plotstate.x.value])
        sl.use_effect(update_y, dependencies=[plotstate.y.value])
        sl.use_effect(update_color, dependencies=[plotstate.color.value])
        sl.use_effect(update_cmap, dependencies=[plotstate.colormap.value])
        sl.use_effect(
            update_log,
            dependencies=[plotstate.logx.value, plotstate.logy.value])
        sl.use_effect(
            update_flip,
            dependencies=[plotstate.flipx.value, plotstate.flipy.value])

    pfig = FigureBokeh(
        p,
        dependencies=[],
        dark_theme=DARKTHEME,
        light_theme=LIGHTTHEME,
    )
    print(p.x_range.start, p.x_range.end)
    print(p.y_range.start, p.y_range.end)

    add_effects(pfig)
    return pfig
