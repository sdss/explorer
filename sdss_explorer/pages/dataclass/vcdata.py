"""Virtual columns dataclass"""

import solara as sl
from .state import State


class VCList:
    """Virtual column data class"""

    # TODO: refactor this to dictionary at some point
    def __init__(self, subset) -> None:
        self.columns = sl.reactive([])
        self.subset = subset  # pointer to parent subset

    def add_column(self, name, expression):
        self.columns.value = self.columns.value + [(name, expression)]

    def delete_column(self, name):
        for n, (colname, _expr) in enumerate(self.columns.value):
            if colname == name:
                q = n
                break
        self.columns.value = self.columns.value[:q] + self.columns.value[q +
                                                                         1:]

    def __repr__(self) -> str:
        return str(dict(self.columns.value))
