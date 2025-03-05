"""Grid layout dataclass"""

import solara as sl

from .state import State


class GridData:
    """
    Class holding current state of grid layout.

    Note:
        All modifying functions are nested as subfunctions of `ObjectGrid`.

    Attributes:
        grid_layout (sl.Reactive[list[dict[str,int]]]): list of grid layout properties per item
        objects (sl.Reactive[list[Any]]): list of widgets to render
        states (sl.Reactive[list[PlotState]]): list of states, for exporting
        index (sl.Reactive[int]): index, used for ensuring unique state between widgets
    """

    def __init__(self, objects=[], layout=[], states=[]) -> None:
        self.grid_layout = sl.reactive(layout)
        self.objects = sl.reactive(objects)
        self.states = sl.reactive(states)
        self.index = sl.reactive(len(objects))

    def __repr__(self) -> str:
        return str({
            "uuid": State.uuid,
            "objects": self.objects.value,
            "layout": self.grid_layout.value,
        })


GridState = GridData()
"""GridData instance for app"""
