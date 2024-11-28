"""Sidebar initialization"""

import solara as sl
import reacton.ipyvuetify as rv

from ...dataclass import State
from .vc_ui import VirtualColumnsPanel
from .glossary import ColumnGlossary
from .subset_ui import SubsetMenu


@sl.component()
def Sidebar():

    with sl.Sidebar() as main:
        SubsetMenu()
        rv.Divider()
        with rv.ExpansionPanels(accordion=True, multiple=True):
            ColumnGlossary()
    return main
