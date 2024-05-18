"""Glossary of columns components for the sidebar"""

import solara as sl
from typing import Union, List, Callable
from solara.alias import rv

from .dialog import Dialog

# NOTE: can be moved to assets directory to keep separate.
md_text = r"""
# Parameter Explorer
The Parameter Explorer is SDSS-V's interface for accessing and exploring Milky Way Mapper stellar parameters provided by Astra for SDSS-V targets. The Explorer is designed to provide a high-speed interface for aggregated statistics and visualizations of filtered _Subsets_ of the SDSS-V database.


Explorer is developed by SDSS-V, using `solara`, `vaex`, and `plotly`. Explorer is developed and maintained by Riley Thai and Brian Cherinka.
"""


@sl.component()
def HelpBlurb():
    """Dialog popup to provide general description of the application."""
    open, set_open = sl.use_state(False)

    with rv.AppBarNavIcon() as main:
        sl.Button(
            icon_name="mdi-help",
            icon=True,
            outlined=True,
            on_click=lambda: set_open(True),
        )
        with Dialog(open, ok=None, title="About", cancel="close"):
            with rv.Card(style_="width: 100%; height: 100%"):
                sl.Markdown(md_text)

    return main
