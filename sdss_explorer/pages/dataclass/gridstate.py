"""Grid layout dataclass"""

import solara as sl


class GridState:
    """
    Class holding current state of grid layout.
    """

    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    index = 0
