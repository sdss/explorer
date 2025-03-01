from typing import Callable

import solara as sl
import time as t
from bokeh.io import curdoc, output_notebook
from bokeh.models import Plot, Model
from bokeh.themes import Theme
from jupyter_bokeh import BokehModel


@sl.component_vue("bokeh_loaded.vue")
def BokehLoaded(loaded: bool, on_loaded: Callable[[bool], None]):
    pass


@sl.component
def FigureBokeh(
    fig,
    light_theme: str | Theme = "light_minimal",
    dark_theme: str | Theme = "dark_minimal",
    dependencies=None,
):
    loaded = sl.use_reactive(False)
    dark = sl.lab.use_dark_effective()
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    fig_element = BokehModel.element(model=fig)

    def update_data():
        fig_widget: BokehModel = sl.get_widget(fig_element)
        fig_model: Plot = fig_widget._model  # base class for figure
        if fig != fig_model:  # don't do on first startup
            # pause until all updates complete
            with fig_model.hold(render=True):
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
                    setattr(fig_model, place, attr[length:])

    def update_theme():
        # NOTE: using bokeh.io.curdoc and this model._document prop will point to the same object
        fig_widget: BokehModel = sl.get_widget(fig_element)
        if dark:
            fig_widget._document.theme = dark_theme
        else:
            fig_widget._document.theme = light_theme

    sl.use_effect(update_data, dependencies or fig)
    sl.use_effect(update_theme, [dark, loaded.value])

    def set_init_theme():
        curdoc().theme = dark_theme if dark else light_theme

    sl.use_memo(set_init_theme, dependencies=[])

    if loaded.value:
        # t.sleep(0.5)  # FORCE LOCKOUT for theme rendering
        return fig_element
    # else:
    #    # NOTE: the returned object will be a v.Sheet until Bokeh is loaded
    #    # BUG: this will show the JS error or even the figure itself temporarily before loading
    #    with sl.Card(margin=0, elevation=0):
    #        with sl.Row(justify="center"):
    #            sl.SpinnerSolara(size="200px")
