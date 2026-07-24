from typing import Callable

import solara as sl
from bokeh.core.serialization import DeserializationError
from bokeh.io import curdoc
from bokeh.models import Plot
from bokeh.plotting import figure
from bokeh.themes import Theme
from jupyter_bokeh import BokehModel


class SafeBokehModel(BokehModel):
    """BokehModel with the upstream teardown faults patched out.

    Both bugs are in jupyter_bokeh 4.1.0 and are patched here rather than in a
    vendored fork, so we can track the pypi release directly.

    """

    def close(self) -> None:
        """Detaches document callbacks only while still registered.

        We have the explicit cleanup callback + solara cleans the widget, but
        ipywidgets calls close() again from gc (via __del__), which raises KeyError
        for an already deleted object
        """
        # skips the BokehModel.close and goes straight to the ipywidgets teardown
        super(BokehModel, self).close()
        document = self._document
        if document is not None:
            registry = getattr(document.callbacks, "_change_callbacks", {})
            if self in registry:  # only remove if we are in the registry
                document.remove_on_change(self)

    def _sync_model(self, model, content, buffers) -> None:
        """Drops frontend events that fail to deserialize.

        An event can reference a model already removed or replaced server side,
        which otherwise raises DeserializationError from ipywidgets
        """
        try:
            super()._sync_model(model, content, buffers)
        except DeserializationError:
            return


@sl.component_vue("bokeh_loaded.vue")
def BokehLoaded(loaded: bool, on_loaded: Callable[[bool], None]):
    pass


@sl.component
def FigureBokeh(
    fig: Plot | figure,
    light_theme: str | Theme = "light_minimal",
    dark_theme: str | Theme = "dark_minimal",
    dependencies=None,
):
    """Generates a Bokeh figure as a solara Jupyter widget.

    Note:
        This is very experimental. You may notice render issues.

    Warning:
        We never use this `dependencies` prop. We do callbacks ourselves for performance.

    Args:
        fig: figure object
        light_theme: theme to use in light mode
        dark_theme: theme to use in dark mode
        dependencies (list[str] | None): dependencies to trigger data updates on.
    """
    loaded = sl.use_reactive(False)
    dark = sl.lab.use_dark_effective()
    BokehLoaded(loaded=loaded.value, on_loaded=loaded.set)
    fig_element = SafeBokehModel.element(model=fig)

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

    def cleanup_widget():
        # explicitly adds a teardown cleanup callback for the widget on unmount
        # the comm and document callbacks are detached manually, rather than on garbage collection
        def cleanup():
            try:
                fig_widget: BokehModel = sl.get_widget(fig_element)
            except Exception:
                return
            if isinstance(fig_widget, BokehModel):
                # close() detaches the doc callbacks + shuts the comm
                fig_widget.close()

        return cleanup

    sl.use_effect(cleanup_widget, dependencies=[])

    def set_init_theme():
        curdoc().theme = dark_theme if dark else light_theme

    sl.use_memo(set_init_theme, dependencies=[])

    # i attempted to make a loading spinner, but it did not work.
    if loaded.value:
        return fig_element
    # else:
    #    # BUG: this will show the JS error or even the figure itself temporarily before loading
    #    with sl.Card(margin=0, elevation=0):
    #        with sl.Row(justify="center"):
    #            sl.SpinnerSolara(size="200px")
