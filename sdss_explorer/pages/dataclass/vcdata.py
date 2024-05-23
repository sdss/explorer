"""Virtual columns dataclass"""

import solara as sl
from .state import State


class VCData:
    """Virtual column data class"""

    columns = sl.reactive(list())

    @staticmethod
    def add_column(name, expression):
        VCData.columns.value.append((name, expression))

    @staticmethod
    def delete_column(name, expression):
        for n, (colname, _expr) in enumerate(VCData.columns.value):
            if colname == name:
                q = n
                break
        State.df.value.delete_virtual_column(name)
        VCData.columns.value = VCData.columns.value[:q] + VCData.columns.value[
            q + 1:]
