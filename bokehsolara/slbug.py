import solara as sl
import reacton.ipyvuetify as rv

from objectgrid import show_plot


@sl.component()
def Page():
    with sl.AppBar():
        sl.lab.ThemeToggle()
    layout, set_layout = sl.use_state([
        {
            "h": 5,
            "i": "0",
            "moved": False,
            "w": 3,
            "x": 0,
            "y": 0
        },
        {
            "h": 5,
            "i": "1",
            "moved": False,
            "w": 5,
            "x": 3,
            "y": 0
        },
        {
            "h": 11,
            "i": "2",
            "moved": False,
            "w": 4,
            "x": 8,
            "y": 0
        },
        {
            "h": 12,
            "i": "3",
            "moved": False,
            "w": 5,
            "x": 0,
            "y": 5
        },
        {
            "h": 6,
            "i": "4",
            "moved": False,
            "w": 3,
            "x": 5,
            "y": 5
        },
        {
            "h": 6,
            "i": "5",
            "moved": False,
            "w": 7,
            "x": 5,
            "y": 11
        },
    ])
    items, set_items = sl.use_state(
        {i: show_plot("scatter", print)
         for i in range(len(layout))})
    sl.GridDraggable(items=items,
                     on_grid_layout=set_layout,
                     grid_layout=layout)


if __name__ == "__main__":
    Page()
