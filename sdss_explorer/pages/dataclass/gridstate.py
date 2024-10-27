"""Grid layout dataclass"""

import solara as sl

from .state import State


class GridData:
    """
    Class holding current state of grid layout.
    """

    def __init__(self) -> None:
        self.objects = sl.reactive([])
        self.grid_layout = sl.reactive([])
        self.index = sl.reactive(0)

    def __repr__(self) -> str:
        return str({
            'uuid': State.uuid,
            'objects': self.objects.value,
            'layout': self.grid_layout.value,
        })


GridState = GridData()
