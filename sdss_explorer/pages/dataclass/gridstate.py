"""Grid layout dataclass"""

import solara as sl


class GridData:
    """
    Class holding current state of grid layout.
    """

    objects = sl.reactive([])
    grid_layout = sl.reactive([])
    index = sl.reactive(0)
