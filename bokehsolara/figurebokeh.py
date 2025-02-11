from typing import Callable

import solara as sl
from bokeh.io import curdoc
from bokeh.models import Plot, Model
from bokeh.themes import Theme
from jupyter_bokeh import BokehModel


@sl.component_vue("bokeh_loaded.vue")
def BokehLoaded(loaded: bool, on_loaded: Callable[[bool], None]):
    pass


@sl.component
def FigureBokeh(
    fig,
    dependencies=None,
    light_theme: str | Theme = "light_minimal",
    dark_theme: str | Theme = "dark_minimal",
):
    loaded = sl.use_reactive(False)
    dark = sl.lab.use_dark_effective()
    fig_key = sl.use_uuid4([])
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    if loaded.value:
        fig_element = BokehModel.element(model=fig).key(
            fig_key)  # TODO: since it isnt hashable it needs a unique key

        def update_data():
            fig_widget: BokehModel = sl.get_widget(fig_element)
            fig_model: Plot = fig_widget._model  # base class for figure
            if fig != fig_model:  # don't do on first startup
                # pause until all updates complete
                fig_model.hold_render = True

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

            return

        def update_theme():
            # NOTE: using bokeh.io.curdoc and this model._document prop will point to the same object
            fig_widget: BokehModel = sl.get_widget(fig_element)
            doc = curdoc()
            if dark:
                doc.theme = dark_theme
                fig_widget._document.theme = dark_theme
            else:
                doc.theme = light_theme
                fig_widget._document.theme = light_theme

        sl.use_effect(update_data, dependencies or fig)
        sl.use_effect(update_theme, [dark, loaded.value])
    else:
        with sl.Card(margin=0, elevation=0) as main:
            with sl.Row(justify="center"):
                sl.SpinnerSolara(size="200px")
