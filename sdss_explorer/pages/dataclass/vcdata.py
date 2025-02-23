"""Virtual columns dataclass"""

import solara as sl
from .state import State
from .subsets import SubsetState


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
        for subset in SubsetState.subsets.value.values():
            if name not in subset.df.virtual_columns.keys():
                subset.df.add_virtual_column(name, expression)

    def delete_column(self, name):
        """Remove a virtual column from the DataFrame."""
        # trigger plot resets FIRST
        columns = self.columns.value.copy()
        columns.pop(name)
        self.columns.set(columns)

        # now delete_virtual_column
        State.df.value.delete_virtual_column(name)
        for subset in SubsetState.subsets.value.values():
            if name in subset.df.virtual_columns.keys():
                subset.df.delete_virtual_column(name)

    def __repr__(self) -> str:
        return str(dict(self.columns.value))


VCData = VCList()
