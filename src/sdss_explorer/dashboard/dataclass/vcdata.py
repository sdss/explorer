"""Virtual columns dataclass"""

import logging
import solara as sl
from .state import State
from .subsets import SubsetState

logger = logging.getLogger("dashboard")


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
                logger.debug("adding vc " + str(name) + " to subset " +
                             str(subset.name))
                subset.df.add_virtual_column(name, expression)

    def delete_column(self, name):
        """Remove a virtual column from the DataFrame."""
        # trigger plot resets FIRST
        columns = self.columns.value.copy()
        columns.pop(name)

        # first, if any other VC's depend on this one, they go first
        removed = [name]
        for other_name in set(
                columns.keys()):  # prevents changing size during iteration
            if name in State.df.value[other_name].variables():
                columns.pop(other_name)  # drop from UI datastruct
                removed.append(other_name)  # save this removal for later

        # remove all in a single update to prevent race conditions
        self.columns.set(columns)

        # now delete all removed virtual columns from dataframe(s)
        for column in removed:
            State.df.value.delete_virtual_column(name)
            for subset in SubsetState.subsets.value.values():
                if column in subset.df.virtual_columns.keys():
                    subset.df.delete_virtual_column(column)

    def __repr__(self) -> str:
        return str(dict(self.columns.value))


VCData = VCList()
