import solara as sl
from solara.lab import Menu
import reacton.ipyvuetify as rv

from plots import show_plot
from plot_settings import show_settings
from state import PlotState


@sl.component
def ViewCard(type, del_func):
    with rv.Card(style_=" width: 100%; height: 100%") as main:
        if type == "table":
            return
        else:
            state = PlotState()
            with rv.CardText():
                btn = sl.Button(icon_name="mdi-settings", block=True)
                with Menu(activator=btn, close_on_content_click=False):
                    with sl.Card(margin=0):
                        show_settings(type, state)
                        sl.Button(
                            icon_name="mdi-delete",
                            color="red",
                            block=True,
                            on_click=del_func,
                        )
                with sl.Column():
                    show_plot(type, state)

    return main


@sl.component
def ObjectGrid():
    objects, set_objects = sl.use_state([])
    grid_layout, set_grid_layout = sl.use_state([])

    def delete_card(i):
        set_grid_layout(grid_layout[0:i] + objects[i:])
        set_objects(objects[0:i] + objects[i:])

    def add_view(objects, type):
        if len(grid_layout) == 0:
            prev = {
                "x": 0,
                "y": -10,
                "w": 12,
                "h": 12,
                "i": -1,
                "moved": False
            }
        else:
            prev = grid_layout[-1]
        grid_layout.append({
            "x": prev["x"],
            "y": prev["y"] + prev["h"] + 4,
            "w": prev["w"],
            "h": prev["h"],
            "i": prev["i"] + 1,
        })

        set_objects(
            objects +
            [ViewCard(type, lambda: delete_card(grid_layout[-1]["i"]))])

    def add_histogram():
        add_view(objects, "histogram")

    def add_histogram2d():
        add_view(objects, "histogram2d")

    def add_scatter():
        add_view(objects, "scatter")

    def add_skyplot():
        add_view(objects, "skyplot")

    def reset_layout():
        set_grid_layout([])
        set_objects([])

    with sl.Column() as main:
        with sl.Columns([7, 1]):
            btn = sl.Button("Add View", icon_name="mdi-image-plus")
            with sl.Column():
                with Menu(activator=btn):
                    with sl.Column(gap="0px"):
                        [
                            sl.Button(label="histogram",
                                      on_click=add_histogram),
                            sl.Button(label="aggregated",
                                      on_click=add_histogram2d),
                            sl.Button(label="table"),
                            sl.Button(label="scatter", on_click=add_scatter),
                            sl.Button(label="skyplot", on_click=add_skyplot),
                        ]
            with sl.Column():
                sl.Button(color="yellow",
                          icon_name="mdi-refresh",
                          on_click=reset_layout)
        sl.GridDraggable(
            items=objects,
            grid_layout=grid_layout,
            on_grid_layout=set_grid_layout,
            resizable=True,
            draggable=False,
        )
    print(grid_layout)
    print(len(objects), " : ", objects)
    return main
