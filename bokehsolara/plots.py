import datashader as ds
import os
from typing import Callable, Optional, cast

import ipyvuetify as v
import ipywidgets as widgets
import numpy as np
import reacton as r
import reacton.ipyvuetify as rv
import solara as sl
import traitlets as t
import vaex as vx
import xarray
from bokeh.io import output_notebook
from bokeh.events import Reset
from bokeh.models import BoxSelectTool, ColorBar, LinearColorMapper, HoverTool
from bokeh.models import CustomJS
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu

from .state import plotstate, df
from .bokeh import FigureBokeh


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
    if bintype == 'count':
        z = z.where(np.abs(z) != 0, np.nan)

    x_edges = z.coords[plotstate.x.value].values
    y_edges = z.coords[plotstate.x.value].values
    return z, x_edges, y_edges, limits


@sl.component()
def Heatmap():

    def create_figure():
        """Creates figure with relevant objects"""
        # obtain data
        z, x_centers, y_centers, limits = get_data()

        # create menu
        menu = BokehMenu(items=[
            ActionItem(
                label='test',  # this isnt visible, how fix?
                action=CustomJS(
                    code=
                    """window.open('https://www.google.com', '_blank').focus()"""
                )  # bound to reactive of last hovered points
            ),
        ])
        menu.styles = {"color": "black", "font-size": "16px"}

        # generate source object
        source = ColumnDataSource(
            data={
                'x': np.repeat(x_centers, len(y_centers)),
                'y': np.tile(y_centers, len(x_centers)),
                'z': z.values.flatten(),
            })

        # generate main figure
        p = figure(
            x_axis_label=plotstate.x.value,
            y_axis_label=plotstate.y.value,
            tools=TOOLS,
            context_menu=menu,
            toolbar_location='above',
            #height_policy='max',
            width_policy='max',
            active_scroll='wheel_zoom',  # default to scroll wheel for zoom
            output_backend=
            'webgl',  # for performance, will fallback to HTML5 if unsupported
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
                'field': 'z',
                'transform': mapper
            })

        # create hovertool, bound to figure object
        TOOLTIPS = [(plotstate.x.value, '$x'), (plotstate.y.value, '$y'),
                    (plotstate.bintype.value, '@z')]
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

    source.selected.on_change('indices', on_select)

    def add_effects(pfig):

        def change_heatmap_data():
            if pfig is not None:
                fig_element: BokehModel = sl.get_widget(pfig)
                z, x_centers, y_centers, limits = get_data()

                # directly update data
                source.data = {
                    'x': np.repeat(x_centers, len(y_centers)),
                    'y': np.tile(y_centers, len(x_centers)),
                    'z': z.values.flatten(),
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
                    'x': np.repeat(x_centers, len(y_centers)),
                    'y': np.tile(y_centers, len(x_centers)),
                    'z': z.values.flatten(),
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
        sl.use_effect(change_heatmap_data,
                      dependencies=[
                          plotstate.color.value,
                          plotstate.bintype.value,
                      ])
        sl.use_effect(change_colormap, dependencies=[plotstate.colormap.value])

    pfig = FigureBokeh(p)
    add_effects(pfig)
    return pfig


@sl.component()
def Scatter():

    def create_figure():
        """Creates figure with relevant objects"""
        # obtain data
        # TODO: categorical support
        z = df[plotstate.color.value].values

        # create menu
        menu = BokehMenu()
        menu.styles = {"color": "black", "font-size": "16px"}

        # generate source objects
        source = ColumnDataSource(
            data={
                'x': df[plotstate.x.value].values,
                'y': df[plotstate.y.value].values,
                'z': z,
                'sdss_id': df['L'].values,  # temp
            })
        hover_source = ColumnDataSource(
            data={'ind': [1, None]})  # 2 length arr to not break bokeh

        # generate main figure
        p = figure(
            x_axis_label=plotstate.x.value,
            y_axis_label=plotstate.y.value,
            tools=TOOLS,
            context_menu=menu,
            toolbar_location='above',
            #height_policy='max',
            width_policy='max',
            active_scroll='wheel_zoom',  # default to scroll wheel for zoom
            output_backend=
            'webgl',  # for performance, will fallback to HTML5 if unsupported
        )

        # setup menu items
        items = [
            ActionItem(label='Go to Target Page',
                       action=CustomJS(args=dict(source=source,
                                                 hover_source=hover_source),
                                       code="""
                    if (hover_source.data.ind[1] !== null) {
                        console.log('loading page');
                        window.open(`https://data.sdss.org/zora/target/${source.data.sdss_id[hover_source.data.ind[1]]}`, '_blank').focus();
                    }
                    """)),
            ActionItem(label='Propagate selection to subset'),  # TODO
            ActionItem(label='Reset plot',
                       action=CustomJS(args=dict(p=p),
                                       code="""p.reset.emit()""")),
        ]
        menu.update(items=items)

        # add hover callback
        cb = CustomJS(args=dict(source=source, hover_source=hover_source),
                      code="""
                      if (source.inspected.indices.length>0){
                          console.log('cb triggered');
                          hover_source.data.ind[1] = source.inspected.indices[0];
                          }
                      """)
        p.js_on_event('mousemove', cb)

        # setup colormap
        # TODO: use factor_cmap for catagorical data
        # TODO: use log_cmap when log is requested
        mapper = LinearColorMapper(
            palette=plotstate.colormap.value,
            low=z.min(),
            high=z.max(),
        )

        # generate scatter points
        glyph = p.scatter(x="x",
                          y="y",
                          source=source,
                          size=8,
                          fill_color={
                              'field': 'z',
                              'transform': mapper
                          })

        # create hovertool, bound to figure object
        TOOLTIPS = [(plotstate.x.value, '$snap_x'),
                    (plotstate.y.value, '$snap_y'),
                    (plotstate.color.value, '@z'), ('sdss_id', '@sdss_id')]
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

    source.selected.on_change('indices', on_select)

    def add_effects(pfig):

        def change_heatmap_data():
            if pfig is not None:
                fig_element: BokehModel = sl.get_widget(pfig)
                z, x_centers, y_centers, limits = get_data()

                # directly update data
                source.data = {
                    'x': np.repeat(x_centers, len(y_centers)),
                    'y': np.tile(y_centers, len(x_centers)),
                    'z': z.values.flatten(),
                }

                # update colorbar
                mapper.low = z.min().item()
                mapper.high = z.max().item()

                return

        def change_xy_data():
            if pfig is not None:
                fig_element: BokehModel = sl.get_widget(pfig)
                z, x_centers, y_centers, limits = get_data()

                # directly update data
                source.data = {
                    'x': np.repeat(x_centers, len(y_centers)),
                    'y': np.tile(y_centers, len(x_centers)),
                    'z': z.values.flatten(),
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
        sl.use_effect(change_heatmap_data,
                      dependencies=[
                          plotstate.color.value,
                          plotstate.bintype.value,
                      ])
        sl.use_effect(change_colormap, dependencies=[plotstate.colormap.value])

    pfig = FigureBokeh(p)
    add_effects(pfig)
    return pfig
