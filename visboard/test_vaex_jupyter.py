import vaex as vx
import numpy as np
import vaex.jupyter.model as vjm

import solara as sl
import plotly.graph_objects as go

df = vx.open("/home/riley/uni/rproj/data/astra-clean.parquet")

# axes definition
extend = 50
x_axis = vjm.Axis(df=df,
                  expression=df.teff,
                  shape=100,
                  min=df.teff.min(),
                  max=df.teff.max())
y_axis = vjm.Axis(df=df,
                  expression=df.logg,
                  shape=100,
                  min=df.logg.min(),
                  max=df.logg.max())


class PlotlyHeatmap:

    def __init__(
        self,
        x_axis,
        y_axis,
        figure_height=500,
        figure_width=400,
        title="Hi vaex, hi plotly",
    ):
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.heatmap = go.Heatmap()
        self.layout = go.Layout(
            height=figure_height,
            width=figure_width,
            title=title,
            xaxis=go.layout.XAxis(title=str(x_axis.expression),
                                  range=[x_axis.min, x_axis.max]),
            yaxis=go.layout.YAxis(title=str(y_axis.expression),
                                  range=[y_axis.min, y_axis.max]),
        )
        self.fig = go.FigureWidget(data=[self.heatmap], layout=self.layout)
        # we respond to zoom/pan
        self.fig.layout.on_change(self._pan_and_zoom, "xaxis.range",
                                  "yaxis.range")

    def _pan_and_zoom(self, layout, xrange, yrange):
        self.x_axis.min, self.x_axis.max = xrange
        self.y_axis.min, self.y_axis.max = yrange

    def __call__(self, data_array):
        ar = data_array.data  # take the numpy array data
        assert data_array.ndim == 2
        dim_x = data_array.dims[0]
        dim_y = data_array.dims[1]
        x0, x1 = (
            data_array.coords[dim_x].attrs["min"],
            data_array.coords[dim_x].attrs["max"],
        )
        y0, y1 = (
            data_array.coords[dim_y].attrs["min"],
            data_array.coords[dim_y].attrs["max"],
        )
        dx = (x1 - x0) / data_array.shape[0]
        dy = (y1 - y0) / data_array.shape[1]

        z = np.log1p(ar).T
        self.fig.update_traces(dict(z=z, x0=x0, y0=y0, dx=dx, dy=dy))
        heatmap_plotly.fig.update_layout(
            xaxis=go.layout.XAxis(title=dim_x, range=[x0, x1]),
            yaxis=go.layout.YAxis(title=dim_y, range=[y0, y1]),
        )


heatmap_plotly = PlotlyHeatmap(x_axis, y_axis)


@sl.component
def Page():
    sl.FigurePlotly(heatmap_plotly.fig)


if __name__ == "__main__":
    Page()
