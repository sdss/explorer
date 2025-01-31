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
from bokeh.themes import Theme
from jupyter_bokeh import BokehModel
from solara.components.file_drop import FileInfo
from solara.lab import Menu


@sl.component_vue("bokeh_loaded.vue")
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
    light_theme: str | Theme = "light_minimal",
    dark_theme: str | Theme = "dark_minimal",
):
    loaded = sl.use_reactive(False)
    dark = sl.lab.use_dark_effective()
    output_notebook(hide_banner=True)
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    if loaded.value:
        fig_element = BokehModel.element(model=fig)
        print(type(fig_element))

        def update_data():
            fig_widget: BokehModel = sl.get_widget(fig_element)

            length = len(fig_widget._model.renderers)
            fig_widget._model.renderers.extend(fig.renderers)
            fig_widget._model.renderers = fig_widget._model.renderers[length:]

            # WARNING: leads to errors
            # fig_widget._model.renderers = fig.renderers

            # WARNING: do not do this ever
            # fig_widget._model = fig

            # WARNING: overwrites model; wrapper method that performs above whilst adjusting render bundle
            # fig_widget.update_from_model(fig)

            # push_notebook(document=fig_widget._document)
            return

        def update_theme():
            # NOTE: using bokeh.io.curdoc and this model._document prop will point to the same object
            # TODO: check if this curdoc prop needs to be updated PER PLOT or PER FIGURE
            fig_widget: BokehModel = sl.get_widget(fig_element)
            if dark:
                fig_widget._document.theme = dark_theme
            else:
                fig_widget._document.theme = light_theme

        sl.use_effect(update_data, dependencies or fig)
        sl.use_effect(update_theme, dark)
        return fig_element
    else:
        with sl.Card(margin=0, elevation=0) as main:
            # NOTE: the card expands to fit space
            with sl.Row(justify="center"):
                sl.SpinnerSolara(size="200px")
