"""Grid layout dataclass"""

import solara as sl

from .state import State


class GridData:
    """
    Class holding current state of grid layout.
    """

    def __init__(self, objects=[], layout=[], states=[]) -> None:
        self.grid_layout = sl.reactive(layout)
        self.objects = sl.reactive(objects)
        self.states = sl.reactive(states)
        self.index = sl.reactive(len(objects))

    def __repr__(self) -> str:
        return str({
            'uuid': State.uuid,
            'objects': self.objects.value,
            'layout': self.grid_layout.value,
        })


GridState = GridData()
