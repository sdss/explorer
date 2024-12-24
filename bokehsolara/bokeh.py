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
