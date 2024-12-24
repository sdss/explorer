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

df = vx.example()[:100_000]

TOOLS = 'pan,wheel_zoom,box_zoom,reset,save'

colormaps = [x for x in colormaps if '256' in x]


def gen_tooltips(state):
    """Helper function to generate tooltips"""
    tooltips = []
    tooltips.append((state.x.value, '$x'))
    tooltips.append((state.y.value, '$y'))
    if plotstate.type.value == 'heatmap':
        tooltips.append((state.bintype.value, '@z'))

    return tooltips


class plotstate:
    type = sl.reactive('heatmap')
    x = sl.reactive('x')
    y = sl.reactive('y')
    bintype = sl.reactive('mean')
    color = sl.reactive('FeH')
    colormap = sl.reactive('Inferno256')
    nbins = sl.reactive(101)
    last_hovered_id = sl.reactive(cast(int, None))


@sl.component_vue('bokeh_loaded.vue')
def BokehLoaded(loaded: bool, on_loaded: Callable[[bool], None]):
    pass


@sl.component
def PlotBokeh(fig: figure):
    loaded = sl.use_reactive(False)
    output_notebook(hide_banner=True)
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    foo = BokehModel(model=fig)
    if loaded.value:
        foo.element(model=fig)
        return foo


def FigureBokeh(
    fig,
    dependencies=None,
):
    fig_element = BokehModel.element(model=fig)
    loaded = sl.use_reactive(False)
    output_notebook(hide_banner=True)
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    if loaded.value:
        fig_element = BokehModel.element(model=fig)

        def update_data():
            fig_widget = sl.get_widget(fig_element)
            model = fig_widget._model
            fig_widget.update_from_model(fig)

            def cleanup():
                # destroy all renderers, then figure object & close widget element
                for renderer in model.renderers:
                    renderer.destroy()
                fig_widget._model.destroy()
                fig_widget.close()
                return

        sl.use_effect(update_data, dependencies or fig)
        return fig_element


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
        TOOLTIPS = [(plotstate.x.value, '$x'), (plotstate.y.value, '$y'),
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


class GridLayout(v.VuetifyTemplate):
    """
    A draggable & resizable grid layout which can be dragged via a toolbar.

    Arguably, this should use solara's components directly, but it
    doesn't function correctly with "component_vue" decorator.
    """

    template_file = os.path.join(os.path.dirname(__file__),
                                 "gridlayout_toolbar.vue")
    gridlayout_loaded = t.Bool(False).tag(sync=True)
    items = t.Union([t.List(), t.Dict()],
                    default_value=[]).tag(sync=True,
                                          **widgets.widget_serialization)
    grid_layout = t.List(default_value=[]).tag(sync=True)
    draggable = t.CBool(True).tag(sync=True)
    resizable = t.CBool(True).tag(sync=True)


GridDraggableToolbar = r.core.ComponentWidget(GridLayout)


class GridState:
    index = sl.reactive(0)
    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    states = sl.reactive([])


dark = True


def show_plot(plottype, *args, **kwargs):
    with rv.Card(
            class_="grey darken-3" if dark else "grey lighten-3",
            style_="width: 100%#; height: 100%",
    ):
        with rv.CardText():
            with sl.Column(
                    classes=["grey darken-3" if dark else "grey lighten-3"]):
                if plottype == 'heatmap':
                    Heatmap()
                else:
                    Scatter()
                btn = sl.Button(
                    icon_name="mdi-settings",
                    outlined=False,
                    classes=["grey darken-3" if dark else "grey lighten-3"],
                )
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        with sl.Columns([1, 1]):
                            sl.Select(label='x',
                                      value=plotstate.x,
                                      values=df.get_column_names())
                            sl.Select(label='x',
                                      value=plotstate.y,
                                      values=df.get_column_names())
                        with sl.Columns([1, 1]):
                            sl.Select(label='color',
                                      value=plotstate.color,
                                      values=df.get_column_names())
                            sl.Select(label='bintype',
                                      value=plotstate.bintype,
                                      values=[
                                          'count', 'mean', 'min', 'max',
                                          'median'
                                      ])
                        sl.Select(
                            label='bintype',
                            value=plotstate.colormap,
                            values=colormaps,
                        )


@sl.component()
def ViewCard(plottype, i, **kwargs):

    def remove(i):
        """
        i: unique identifier key, position in objects list
        q: specific, adaptive index in grid_objects (position dict)
        """
        # find where in grid_layout has key (i)
        for n, obj in enumerate(GridState.grid_layout.value):
            if obj["i"] == i:
                q = n
                break

        # cut layout and states at that spot
        GridState.grid_layout.value = (GridState.grid_layout.value[:q] +
                                       GridState.grid_layout.value[q + 1:])
        GridState.states.value = (GridState.states.value[:q] +
                                  GridState.states.value[q + 1:])

        # replace the object in object list with a dummy renderable
        # INFO: cannot be deleted because it breaks all renders
        GridState.objects.value[i] = rv.Card()

    show_plot(plottype, lambda: remove(i), **kwargs)  # plot shower

    return


def add_view(plottype, layout: Optional[dict] = None, **kwargs):
    """Add a view to the grid. Layout can be parsed as a pre-made dict"""
    if layout is None:
        if len(GridState.grid_layout.value) == 0:
            prev = {"x": 0, "y": -12, "h": 12, "w": 12, "moved": False}
        else:
            prev = GridState.grid_layout.value[-1]
        # TODO: better height logic
        if plottype == "stats":
            height = 7
        else:
            height = 10
        # horizontal or vertical offset depending on width
        if 12 - prev["w"] - prev["x"] >= 6:
            # beside
            x = prev["x"] + 6
            y = prev["y"]
        else:
            # the row below
            x = 0
            y = prev["y"] + prev["h"] + 4
        layout = {
            "x": x,
            "y": y,
            "w": 6,
            "h": height,
            "moved": False,
        }

    # always update with current index
    i = GridState.index.value
    layout.update({"i": i})

    # add and update state vars
    GridState.grid_layout.value.append(layout)
    GridState.index.value += 1

    GridState.objects.value = GridState.objects.value + [
        ViewCard(plottype, i, **kwargs)
    ]


@sl.component()
def ObjectGrid():

    def set_grid_layout(data):
        GridState.grid_layout.value = data

    # WARNING: this is a janky workaround to a solara bug where
    # this will likely have to be changed in future.
    # BUG: it appears to incorrectly NOT reset the grid_layout reactive between different user instances/dev reset
    # don't know what's happening, but it appears to run some threads
    # below fix via thread solves it
    def monitor_grid():
        """Check to ensure length of layout spec is not larger than the number of objects.

        Solves a solara bug where global reactives do not appear to reset."""

        if len(GridState.objects.value) != len(GridState.grid_layout.value):
            while len(GridState.grid_layout.value) > len(
                    GridState.objects.value):
                GridState.grid_layout.value.pop(-1)
            GridState.index.value = len(GridState.objects.value)

    sl.use_thread(
        monitor_grid,
        dependencies=[GridState.objects.value, GridState.grid_layout.value],
    )

    with sl.Column(style={"width": "100%"}) as main:
        with sl.Row():
            btn = sl.Button(
                "Add View",
                outlined=False,
                icon_name="mdi-image-plus",
            )
            with Menu(activator=btn):
                with sl.Column(gap="0px"):
                    [
                        sl.Button(label="histogram",
                                  on_click=lambda: add_view("histogram")),
                        sl.Button(label="heatmap",
                                  on_click=lambda: add_view("heatmap")),
                        sl.Button(label="stats",
                                  on_click=lambda: add_view("stats")),
                        sl.Button(label="scatter",
                                  on_click=lambda: add_view("scatter")),
                        sl.Button(label="skyplot",
                                  on_click=lambda: add_view("skyplot")),
                        # TODO: fix delta2d
                        # BUG: delta2d is currently broken in many ways i need to fix
                        # sl.Button(
                        #    label="delta2d",
                        #    on_click=lambda: add_view("delta2d"),
                        #    disabled=True if n_subsets <= 1 else False,
                        # ),
                    ]
            rv.Spacer()

        GridDraggableToolbar(
            items=GridState.objects.value,
            grid_layout=GridState.grid_layout.value,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=True,
        )
    return main


@sl.component
def Page():
    if df is not None:
        ObjectGrid()
    else:
        sl.Info('help')
