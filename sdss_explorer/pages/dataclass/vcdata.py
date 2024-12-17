"""Virtual columns dataclass"""

import solara as sl
from .state import State


class VCList:
    """Virtual column data class"""

    def __init__(self) -> None:
        self.columns = sl.reactive({})

    def add_column(self, name, expression):
        columns = self.columns.value.copy()
        columns.update({name: expression})
        self.columns.set(columns)
        State.df.value.add_virtual_column(name, expression)

    def delete_column(self, name):
        State.df.value.delete_virtual_column(name)
        columns = self.columns.value.copy()
        columns.pop(name)
        self.columns.set(columns)

    def __repr__(self) -> str:
        return str(dict(self.columns.value))


VCData = VCList()
