"""Grid layout dataclass"""

import solara as sl
from typing import Optional

from .state import State


class GridData:
    """
    Class holding current state of grid layout.

    Note:
        All modifying functions are nested as subfunctions of `ObjectGrid`.

    Attributes:
        grid_layout (sl.Reactive[list[dict[str,int]]]): list of grid layout properties per item
        objects (sl.Reactive[list[Any]]): list of widgets to render
        toolbar_objects (sl.Reactive[list[Any]]): list of toolbar widgets to render in each grid item's top bar
        states (sl.Reactive[list[PlotState]]): list of states, for exporting
        index (sl.Reactive[int]): index, used for ensuring unique state between widgets
    """

    def __init__(
        self,
        objects: Optional[list] = None,
        toolbar_objects: Optional[list] = None,
        layout: Optional[list] = None,
        states: Optional[list] = None,
    ) -> None:
        objects = objects or []
        toolbar_objects = toolbar_objects or []
        layout = layout or []
        states = states or []
        self.grid_layout = sl.reactive(layout)
        self.objects = sl.reactive(objects)
        self.toolbar_objects = sl.reactive(toolbar_objects)
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
