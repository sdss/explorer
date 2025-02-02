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
import traitlets as t
import vaex as vx
import xarray
from bokeh.io import output_notebook, curdoc, push_notebook
from bokeh.events import Reset
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
)
from state import plotstate, df
from figurebokeh import FigureBokeh

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,examine"

colormaps = [x for x in colormaps if "256" in x]

# https://docs.bokeh.org/en/latest/docs/user_guide/interaction/js_callbacks.html#customjs-for-topics-events

DARKTHEME = Theme(
    json={
        "attrs": {
            "Plot": {
                "background_fill_color": "#212121",  # grey-darken-3
                "border_fill_color": "#424242",
                "outline_line_color": "#616161",  # darken-2
            },
            "Axis": {
                "major_tick_line_color": "#FFFFFF",  # White ticks for contrast
                "minor_tick_line_color": "#BDBDBD",  # grey-lighten-1
                "axis_line_color": "#BDBDBD",
                "major_label_text_color": "#FFFFFF",  # White for labels
                "axis_label_text_color": "#FFFFFF",  # White for labels
                "axis_label_text_font_size": "16pt",
            },
            "Grid": {
                "grid_line_color": "#616161",  # grey-darken-2 (x/y grid)
            },
            "Title": {
                "text_color": "#FFFFFF",  # White text
                "text_font_size": "16pt",
            },
            "Legend": {
                "background_fill_color": "#424242",
                "label_text_color": "#FFFFFF",  # White legend labels
            },
            "ColorBar": {
                "background_fill_color": "#424242",
                "title_text_color": "#FFFFFF",
                "major_label_text_color": "#FFFFFF",
            },
            "Text": {
                "text_color": "#FFFFFF",
            },
        }
    })
LIGHTTHEME = Theme(
    json={
        "attrs": {
            "Plot": {
                "background_fill_color":
                "#FAFAFA",  # grey-lighten-3 (paper_bgcolor)
                "border_fill_color": "#EEEEEE",
                "outline_line_color": "#BDBDBD",  # lighten-1
            },
            "Axis": {
                "major_tick_line_color":
                "#212121",  # grey-darken-4 (dark ticks for contrast)
                "minor_tick_line_color": "#616161",  # grey-darken-2
                "axis_line_color": "#616161",
                "major_label_text_color": "#212121",  # grey-darken-4
                "axis_label_text_color": "#212121",  # grey-darken-4
                "axis_label_text_font_size": "16pt",
            },
            "Grid": {
                "grid_line_color": "#BDBDBD",  # grey-lighten-1 (x/y grid)
            },
            "Title": {
                "text_color": "#212121",  # grey-darken-4
                "text_font_size": "16pt",
            },
            "Legend": {
                "background_fill_color": "#EEEEEE",
                "label_text_color": "#212121",  # grey-darken-4
            },
            "ColorBar": {
                "background_fill_color": "#EEEEEE",
                "title_text_color": "#212121",
                "major_label_text_color": "#212121",
            },
            "Text": {
                "text_color": "#212121",
            },
        }
    })


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

                # TODO: force trigger a reset somehow???
                Reset(model=fig_element._model)

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


@sl.component()
def ScatterPlot():
    dark = sl.lab.use_dark_effective()

    def generate_tooltips(plotstate):
        return (f"""
        <div>
        {plotstate.x.value}: $snap_x
        {plotstate.y.value}: $snap_x
        {plotstate.color.value}: @z
        sdss_id: @sdss_id
        </div>\n""" + """
        <style>
        div.bk-tooltip-content > div > div:not(:first-child) {
            display:none !important;
        } 
        </style>
        """)

    def create_figure():
        """Creates figure with relevant objects"""
        p, menu = generate_plot(plotstate)
        source = ColumnDataSource(
            data={
                "x": df[plotstate.x.value].values,
                "y": df[plotstate.y.value].values,
                "z": df[plotstate.color.value].values,
                "sdss_id": df["L"].values,  # temp
            })
        # generate axes
        xaxis, yaxis, grid_x, grid_y = generate_axes(plotstate)

        p.add_layout(xaxis, "below")
        p.add_layout(yaxis, "left")
        p.add_layout(grid_x)
        p.add_layout(grid_y)

        # generate scatter points
        mapper, cb = generate_color_mapper_bar(
            plotstate, df[plotstate.color.value].values)
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
        # TODO: fix css styling
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

        return p, source, mapper, menu, cb

    p, source, mapper, menu, cb = sl.use_memo(
        create_figure,
        dependencies=[
            plotstate.logx.value,
            plotstate.logy.value,
        ],
    )

    def add_effects(pfig):

        def update_x():
            # TODO: ensure no catagorical data failure
            # update CDS
            if pfig is not None:
                fig_widget: BokehModel = sl.get_widget(pfig)
                fig_model: plot = fig_widget._model
                source.data["x"] = df[plotstate.x.value].values

                # replace grid and axes objects
                fig_model.below[0].axis_label = plotstate.x.value
                p.below[0].axis_label = plotstate.x.value

        def update_y():
            # TODO: ensure no catagorical data failure
            # update CDS
            if pfig is not None:
                fig_widget: BokehModel = sl.get_widget(pfig)
                fig_model: plot = fig_widget._model
                source.data["y"] = df[plotstate.y.value].values
                fig_model.left[0].axis_label = plotstate.y.value
                p.left[0].axis_label = plotstate.y.value

        def update_color():
            # TODO: ensure no catagorical data failure
            if pfig is not None:
                fig_widget: BokehModel = sl.get_widget(pfig)
                fig_model: plot = fig_widget._model
                z = df[plotstate.color.value].values
                source.data["z"] = z
                mapper.update(low=z.min(), high=z.max())
                cb.title = plotstate.color.value

        def update_cmap():
            if pfig is not None:
                fig_widget: BokehModel = sl.get_widget(pfig)
                fig_model: plot = fig_widget._model
                mapper.palette = plotstate.colormap.value

        def update_flip():
            if pfig is not None:
                fig_widget: BokehModel = sl.get_widget(pfig)
                fig_model: plot = fig_widget._model
                # TODO: catagorical support
                fig_model.x_range.start = (df[plotstate.x.value].min()[()]
                                           if not plotstate.flipx.value else
                                           df[plotstate.x.value].max()[()])
                fig_model.x_range.end = (df[plotstate.x.value].max()[()]
                                         if not plotstate.flipx.value else
                                         df[plotstate.x.value].min()[()])
                fig_model.y_range.start = (df[plotstate.y.value].min()[()]
                                           if not plotstate.flipy.value else
                                           df[plotstate.y.value].max()[()])
                fig_model.y_range.end = (df[plotstate.y.value].max()[()]
                                         if not plotstate.flipy.value else
                                         df[plotstate.y.value].min()[()])
                fig_model.x_range.flipped = plotstate.flipx.value
                fig_model.y_range.flipped = plotstate.flipy.value

        def update_log():
            if pfig is not None:
                fig_widget: BokehModel = sl.get_widget(pfig)

        sl.use_effect(update_x, dependencies=[plotstate.x.value])
        sl.use_effect(update_y, dependencies=[plotstate.y.value])
        sl.use_effect(update_color, dependencies=[plotstate.color.value])
        sl.use_effect(update_cmap, dependencies=[plotstate.colormap.value])
        # sl.use_effect(
        #    update_log,
        #    dependencies=[plotstate.logx.value, plotstate.logy.value])
        sl.use_effect(
            update_flip,
            dependencies=[plotstate.flipx.value, plotstate.flipy.value])

    pfig = FigureBokeh(p,
                       dependencies=[p],
                       dark_theme=DARKTHEME,
                       light_theme=LIGHTTHEME)
    add_effects(pfig)
    return pfig
