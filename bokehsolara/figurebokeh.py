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
from bokeh.io import output_notebook, curdoc, push_notebook
from bokeh.events import Reset
from bokeh.models import BoxSelectTool, ColorBar, LinearColorMapper, HoverTool
from bokeh.models import CustomJS
from bokeh.palettes import __palettes__ as colormaps
from bokeh.models.ui import ActionItem, Menu as BokehMenu
from bokeh.plotting import ColumnDataSource, figure
from bokeh.models import Plot
from bokeh.themes import Theme
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu


@sl.component_vue("bokeh_loaded.vue")
def BokehLoaded(loaded: bool, on_loaded: Callable[[bool], None]):
    pass


@sl.component
def PlotBokeh(fig: Plot | figure):
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
    light_theme: str | Theme = "light_minimal",
    dark_theme: str | Theme = "dark_minimal",
):
    loaded = sl.use_reactive(False)
    dark = sl.lab.use_dark_effective()
    fig_key = sl.use_uuid4([])
    output_notebook(hide_banner=True)
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    if loaded.value:
        fig_element = BokehModel.element(model=fig).key(
            fig_key)  # TODO: since it isnt hashable it needs a unique key

        def update_data():
            fig_widget: BokehModel = sl.get_widget(fig_element)
            fig_model: Plot = fig_widget._model  # base class for figure
            print("internal FigureBokeh update data triggered")
            if fig != fig_model:
                # pause until all updates complete
                fig_model.hold_render = True

                # if the figure is regenerated, the tool callbacks will break. we have no idea whic
                fig_model.remove_tools(*fig_model.toolbar.tools)
                fig_model.add_tools(*fig.toolbar.tools)

                # this fixes if a user sets default tools in the toolbar
                # NOTE: not exactly perfect; will reset it to whatever the default init was
                #     (i.e. default LMB was pan, switch to box select, will reset back to pan after rerender)
                for active in [
                        "active_drag",
                        "active_inspect",
                        "active_multi",
                        "active_scroll",
                        "active_tap",
                ]:
                    attr = getattr(fig_model.toolbar, active)
                    newattr = getattr(fig.toolbar, active)
                    if attr != "auto":
                        setattr(fig_model.toolbar, active, newattr)

                # extend renderer set and cull previous
                length = len(fig_model.renderers)
                fig_model.renderers.extend(fig.renderers)
                fig_model.renderers = fig_model.renderers[length:]

                # similarly update plot layout properties
                places = ["above", "below", "center", "left", "right"]
                for place in places:
                    attr = getattr(fig_model, place)
                    newattr = getattr(fig, place)
                    length = len(attr)
                    attr.extend(newattr)
                    if place == "right":
                        fig_model.hold_render = False
                    setattr(fig_model, place, attr[length:])

            # WARNING: just breaks
            # fig_widget._model.renderers = fig.renderers

            # WARNING: instead of orphaning, this gives it two parents, which we do not want
            # fig_widget._model = fig

            # WARNING: this does above but also render bundle; leads to widget KeyError on close/shutdown
            # fig_widget.update_from_model(fig)
            return

        def update_theme():
            # NOTE: using bokeh.io.curdoc and this model._document prop will point to the same object
            fig_widget: BokehModel = sl.get_widget(fig_element)
            print(curdoc())
            if dark:
                curdoc().theme = dark_theme
                fig_widget._document.theme = dark_theme
            else:
                curdoc().theme = light_theme
                fig_widget._document.theme = light_theme

        sl.use_effect(update_data, dependencies or fig)
        sl.use_effect(update_theme, [dark, loaded.value])
        return fig_element
    else:
        # NOTE: we don't return this as to not break effect callbacks outside this function; reacton a
        with sl.Card(margin=0, elevation=0) as main:
            # NOTE: the card expands to fit space
            with sl.Row(justify="center"):
                sl.SpinnerSolara(size="200px")
