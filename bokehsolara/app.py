import solara as sl
from bokeh.io import output_notebook

from objectgrid import ObjectGrid
from editor import ExprEditor


@sl.component
def Page():
    output_notebook(hide_banner=True)
    ExprEditor()
    ObjectGrid()

    # if df is not None:
    # else:
    #    sl.Info("help")
