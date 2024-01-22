import vaex as vx
import solara as sl
from solara.lab import ContextMenu
import plotly.graph_objects as go


@sl.component()
def Page():
    df = vx.example()
    hovered, set_hovered = sl.use_state(False)
    clicked, set_clicked = sl.use_state(False)

    dff = df
    dff = dff[:3_000]

    x = dff["x"]
    y = dff["y"]
    fig = go.Figure(data=go.Scattergeo(
        lat=x.values,
        lon=y.values,
        mode="markers",
    ), )

    fig.update_geos(
        bgcolor="#ccc",
        projection_type="aitoff",
        visible=False,
    )
    fig.update_layout(showlegend=False,
                      margin={
                          "t": 30,
                          "b": 10,
                          "l": 0,
                          "r": 0
                      })
    """
    Context Menu handlers
    """

    def on_click(data):
        set_clicked(True)

    def on_hover(data):
        set_clicked(False)
        set_hovered(True)

    def on_unhover(data):
        if not clicked:
            set_hovered(False)

    fig = sl.FigurePlotly(
        fig,
        on_click=on_click,
        on_hover=on_hover,
        on_unhover=on_unhover,
        dependencies=[
            filter,
        ],
    )

    with ContextMenu(activator=fig):
        print(clicked, hovered)
        if clicked & hovered:
            text = "clicked and hovered"
        if clicked and not hovered:
            text = "clicked, not hovered"
        if hovered and not clicked:
            text = "not clicked, hovered"
        else:
            text = "neither"
        sl.Column(
            gap="0px",
            children=[sl.Card(title=text)],
        )
    return


if __name__ == "__main__":
    Page()
