"""Virtual columns dataclass"""

import solara as sl
from .state import State


class VCList:
    """Virtual column data class"""

    def __init__(self) -> None:
        self.columns = sl.reactive({})

    def add_column(self, name, expression):
        """Add a virtual column to the DataFrame."""
        columns = self.columns.value.copy()
        columns.update({name: expression})
        self.columns.set(columns)
        State.df.value.add_virtual_column(name, expression)

    def delete_column(self, name):
        """Remove a virtual column from the DataFrame."""
        State.df.value.delete_virtual_column(name)
        columns = self.columns.value.copy()
        columns.pop(name)
        self.columns.set(columns)

    def __repr__(self) -> str:
        return str(dict(self.columns.value))


VCData = VCList()
