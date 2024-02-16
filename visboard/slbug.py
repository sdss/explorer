import vaex as vx
import solara as sl
from solara.lab import ContextMenu
from plotly.graph_objs._figurewidget import FigureWidget
import plotly.graph_objects as go
import numpy as np

df_loaded = vx.open("/home/riley/rproj/data/apogeenet.parquet")
df = df_loaded.shuffle()


def range_loop(start, offset):
    return (start + (offset % 360) + 360) % 360


DARK_TEMPLATE = dict(layout=go.Layout(
    font=dict(color="white", size=16),
    showlegend=False,
    paper_bgcolor="#424242",
    autosize=True,
    plot_bgcolor="#212121",
    margin={
        "t": 30,
        "b": 80,
        "l": 80,
        "r": 80
    },
))


class PlotState:
    """
    Combination of reactive states which instantiate a specific plot's settings/properties
    """

    def __init__(self, type):
        # common settings
        self.x = sl.use_reactive("teff")
        self.flipx = sl.use_reactive(False)
        self.flipy = sl.use_reactive(False)

        # moderately unique plot parameters/settings
        if type != "histogram":
            self.y = sl.use_reactive("logg")
            self.color = sl.use_reactive("fe_h")
            self.colorscale = sl.use_reactive("viridis")
        if type != "aggregated" and type != "skyplot":
            self.logx = sl.use_reactive(False)
            self.logy = sl.use_reactive(False)

        # statistics settings
        if type == "aggregated" or type == "histogram":
            self.nbins = sl.use_reactive(200)
            if type == "aggregated":
                self.bintype = sl.use_reactive("mean")
                self.binscale = sl.use_reactive(None)
            else:
                self.norm = sl.use_reactive(None)

        # skyplot settings
        if type == "skyplot":
            self.geo_coords = sl.use_reactive("ra/dec")
            self.projection = sl.use_reactive("hammer")

        # all lookup data for types
        # TODO: move this lookup data elsewhere to reduce the size of the plotstate objects
        self.Lookup = dict(
            norms=[
                None, "percent", "probability", "density",
                "probability density"
            ],
            bintypes=["count", "mean", "median", "min", "max"],
            colorscales=[
                "inferno",
                "viridis",
                "jet",
                "solar",
                "plotly3",
                "sunset",
                "sunsetdark",
                "tropic",
                "delta",
                "twilight",
            ],
            binscales=[None, "log1p", "log10"],
            projections=[
                "albers",
                "aitoff",
                "azimuthal equal area",
                "equal earth",
                "hammer",
                "mollweide",
                "mt flat polar quartic",
            ],
        )


@sl.component()
def scatter_menu(plotstate):
    columns = list(map(str, df.columns))
    with sl.Columns([1, 1]):
        with sl.Card(margin=0):
            with sl.Columns([1, 1]):
                sl.Select(
                    "Column x",
                    values=columns,
                    value=plotstate.x,
                )
                sl.Select(
                    "Column y",
                    values=columns,
                    value=plotstate.y,
                )
            sl.Select(
                label="Color",
                values=columns,
                value=plotstate.color,
            )
            sl.Select(
                label="Colorscale",
                values=plotstate.Lookup["colorscales"],
                value=plotstate.colorscale,
            )
        with sl.Card(margin=0):
            with sl.Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                    sl.Switch(label="Log x", value=plotstate.logx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)
                    sl.Switch(label="Log y", value=plotstate.logy)


@sl.component()
def sky_menu(plotstate):
    columns = list(map(str, df.columns))
    with sl.Columns([1, 1]):
        with sl.Card(margin=0):
            with sl.Column():
                sl.ToggleButtonsSingle(value=plotstate.geo_coords,
                                       values=["ra/dec", "galactic lon/lat"])
                sl.Select(
                    label="Projection",
                    value=plotstate.projection,
                    values=plotstate.Lookup["projections"],
                )
            with sl.Row():
                sl.Select(
                    label="Color",
                    values=columns,
                    value=plotstate.color,
                )
                sl.Select(
                    label="Colorscale",
                    values=plotstate.Lookup["colorscales"],
                    value=plotstate.colorscale,
                )
        with sl.Card(margin=0):
            with sl.Columns([1, 1]):
                with sl.Column():
                    sl.Switch(label="Flip x", value=plotstate.flipx)
                with sl.Column():
                    sl.Switch(label="Flip y", value=plotstate.flipy)


@sl.component()
def scatter(plotstate):
    relayout, set_relayout = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)

    def update_filter():
        xfilter = None
        yfilter = None
        try:
            min = relayout["xaxis.range[0]"]
            max = relayout["xaxis.range[1]"]
            xfilter = df[
                f"(({plotstate.x.value} > {np.min((min,max))}) & ({plotstate.x.value} < {np.max((min,max))}))"]
        except KeyError:
            pass
        try:
            min = relayout["yaxis.range[0]"]
            max = relayout["yaxis.range[1]"]
            yfilter = df[
                f"(({plotstate.y.value} > {np.min((min,max))}) & ({plotstate.y.value} < {np.max((min,max))}))"]

        except KeyError:
            pass
        try:
            set_local_filter(xfilter & yfilter)
        except ValueError:
            try:
                set_local_filter(xfilter)
            except ValueError:
                set_local_filter(yfilter)

    sl.use_thread(update_filter, dependencies=[relayout])

    if local_filter is not None:
        dff = df[local_filter]
    else:
        dff = df

    if len(dff) > 20000:
        dff = dff[:20_000]

    def create_fig():
        x = dff[plotstate.x.value].values
        y = dff[plotstate.y.value].values
        c = dff[plotstate.color.value].values
        ids = dff["sdss_id"].values
        figure = go.Figure(
            data=go.Scattergl(
                x=x,
                y=y,
                mode="markers",
                customdata=ids,
                hovertemplate=f"<b>{plotstate.x.value}</b>:" +
                " %{x:.6f}<br>" + f"<b>{plotstate.y.value}</b>:" +
                " %{y:.6f}<br>" + f"<b>{plotstate.color.value}</b>:" +
                " %{marker.color:.6f}<br>" + "<b>ID</b>:" +
                " %{customdata:.d}",
                name="",
                marker=dict(
                    color=c,
                    colorbar=dict(title=plotstate.color.value),
                    colorscale=plotstate.colorscale.value,
                ),
            ),
            layout=go.Layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
                template=DARK_TEMPLATE,
                coloraxis=dict(
                    cmin=np.float32(dff.min(plotstate.color.value)),
                    cmax=np.float32(dff.max(plotstate.color.value)),
                ),
            ),
        )
        return figure

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    def add_effects(fig_element: sl.Element):

        def set_flip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=True)

        def set_log():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.logx.value:
                fig_widget.update_xaxes(type="log")
            else:
                fig_widget.update_xaxes(type="linear")
            if plotstate.logy.value:
                fig_widget.update_yaxes(type="log")
            else:
                fig_widget.update_yaxes(type="linear")

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            data = fig_widget.data[0]
            data.x = dff[plotstate.x.value].values
            data.y = dff[plotstate.y.value].values
            data.marker = dict(
                color=dff[plotstate.color.value].values,
                colorbar=dict(title=plotstate.color.value),
                colorscale=plotstate.colorscale.value,
            )
            fig_widget.update_layout(
                xaxis_title=plotstate.x.value,
                yaxis_title=plotstate.y.value,
            )

        sl.use_effect(
            update_data,
            dependencies=[
                local_filter,
                plotstate.x.value,
                plotstate.y.value,
                plotstate.color.value,
                plotstate.colorscale.value,
            ],
        )
        sl.use_effect(
            set_flip,
            dependencies=[plotstate.flipx.value, plotstate.flipy.value])
        sl.use_effect(
            set_log, dependencies=[plotstate.logx.value, plotstate.logy.value])

    """
    relayout callback
    """

    def on_relayout(data):
        if data is not None:
            # full limit reset, resetting relayout data + local filter
            if "xaxis.autorange" in data["relayout_data"].keys():
                set_relayout({})
                set_local_filter(None)
            # Update the current dictionary
            else:
                set_relayout(dict(relayout, **data["relayout_data"]))

    fig_el = sl.FigurePlotly(figure, on_relayout=on_relayout)
    add_effects(fig_el)


@sl.component()
def skyplot(plotstate):
    relayout, set_relayout = sl.use_state({})
    local_filter, set_local_filter = sl.use_state(None)

    def update_filter():
        try:
            scale = relayout["geo.projection.scale"]
            if scale < 1.0:
                return
        except KeyError:
            scale = 1.0
        try:
            lon_center = relayout["geo.center.lon"]
        except KeyError:
            lon_center = 0
        try:
            lat_center = relayout["geo.center.lat"]
        except KeyError:
            lat_center = 0

        lonlow, lonhigh = (
            range_loop(0, -180 / scale + lon_center),
            range_loop(0, 180 / scale + lon_center),
        )
        latlow, lathigh = (
            np.max((lat_center - (90 / scale), -90)),
            np.min((lat_center + (90 / scale), 90)),
        )

        lonfilter = None
        if scale > 1:
            if lonhigh < lonlow:
                lonfilter = df[f"(ra > {lonlow})"] | df[f"(ra < {lonhigh})"]
            else:
                lonfilter = df[f"(ra > {lonlow})"] & df[f"(ra < {lonhigh})"]
        if lonfilter is not None:
            set_local_filter((df[f"(dec > {latlow})"]
                              & df[f"(dec< {lathigh})"]) & lonfilter)
        else:
            set_local_filter(df[f"(dec > {latlow})"] & df[f"(dec< {lathigh})"])

    sl.use_thread(update_filter, dependencies=[relayout])

    if local_filter is not None:
        dff = df[local_filter]
    else:
        dff = df

    dff = dff[:3_000]

    def create_fig():
        dtick = 30  # for tickers
        lon = dff["ra"]
        lat = dff["dec"]
        figure = go.Figure(data=go.Scattergeo(
            lat=lat.values,
            lon=lon.values,
            mode="markers",
        ), )
        x = list(range(0, 360 + dtick, dtick))
        y = list(range(-90, 90 + dtick, dtick))
        xpos = 0
        ypos = 0
        figure.add_trace(
            go.Scattergeo({
                "lon": x + [xpos] * (len(y)),
                "lat": [ypos] * (len(x)) + y,
                "showlegend": False,
                "text": x + y,
                "mode": "text",
            }))

        figure.update_geos(
            bgcolor="#ccc",
            projection_type="mollweide",
            visible=False,
            lonaxis_showgrid=True,
            lonaxis_tick0=0,
            lataxis_showgrid=True,
            lataxis_tick0=0,
        )
        figure.update_layout(template=DARK_TEMPLATE, )
        return figure

    # only instantiate the figure once
    figure = sl.use_memo(create_fig, dependencies=[])

    print(plotstate.flipx.value)

    def add_effects(fig_element: sl.Element):

        def set_flip():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            if plotstate.flipx.value:
                fig_widget.update_xaxes(autorange="reversed")
            else:
                fig_widget.update_xaxes(autorange=True)
            if plotstate.flipy.value:
                fig_widget.update_yaxes(autorange="reversed")
            else:
                fig_widget.update_yaxes(autorange=True)

        def set_log():
            fig_widget: FigureWidget = sl.get_widget(fig_element)

        def update_data():
            fig_widget: FigureWidget = sl.get_widget(fig_element)
            data = fig_widget.data[0]
            data.lon = dff["ra"].values
            data.lat = dff["dec"].values

        sl.use_effect(update_data, dependencies=[local_filter])
        sl.use_effect(
            set_flip,
            dependencies=[plotstate.flipx.value, plotstate.flipy.value])

    """
    relayout callback
    """

    def on_relayout(data):
        if data is not None:
            # full limit reset, resetting relayout data + local filter
            if "geo.fitbounds" in data["relayout_data"].keys():
                set_relayout({})
                set_local_filter(None)
            # Update the current dictionary
            else:
                set_relayout(dict(relayout, **data["relayout_data"]))

    fig_el = sl.FigurePlotly(figure, on_relayout=on_relayout)
    add_effects(fig_el)


def nest():
    with sl.Columns([1, 1]):
        with sl.Column():
            plotstate = PlotState("skyplot")
            skyplot(plotstate)
            sky_menu(plotstate)
        with sl.Column():
            plotstate2 = PlotState("scatter")
            scatter(plotstate2)
            scatter_menu(plotstate2)


@sl.component()
def Page():
    nest()


if __name__ == "__main__":
    Page()
