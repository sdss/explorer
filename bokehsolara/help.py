import solara as sl
import vaex as vx
import plotly.express as px


@sl.component()
def Page():
    count = sl.use_reactive(0)
    sl.Button(label="count", on_click=lambda: count.set(count.value + 1))
    fig = sl.use_memo(
        lambda: px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16]),
        dependencies=[])

    def add_effect(thing):

        def show_layout():
            fig_widget = sl.get_widget(thing)
            print(fig_widget)
            print(thing)

        sl.use_effect(show_layout, dependencies=[count.value])

    thing = sl.FigurePlotly(fig)
    add_effect(thing)


if __name__ == "__main__":
    Page()
