"""Sidebar initialization"""

import solara as sl
import reacton.ipyvuetify as rv

from ...dataclass import State
from .vc_ui import VirtualColumnsPanel
from .glossary import ColumnGlossary
from .subset_ui import SubsetMenu


@sl.component()
def Sidebar():
    df = State.df.value

    with sl.Sidebar() as main:
        if df is not None:
            SubsetMenu()
            rv.Divider()
            with rv.ExpansionPanels(accordion=True, multiple=True):
                VirtualColumnsPanel()
                ColumnGlossary()
        else:
            sl.Info("No data loaded.")
    return main
