"""Components to assist with user information, including about the app,"""

import solara as sl
from typing import Union, List, Callable
from solara.alias import rv

from .state import State
from .dialog import Dialog

# NOTE: can be moved to assets directory to keep separate.
md_text = r"""
### Parameter Explorer
The Parameter Explorer is SDSS-V's interface for accessing and exploring Milky Way Mapper stellar parameters provided by Astra for SDSS-V targets. The Explorer is designed to provide a high-speed interface for aggregated statistics and visualizations of filtered _Subsets_ of the SDSS-V database.


Explorer is developed by SDSS-V, using `solara`, `vaex`, and `plotly`. Explorer was developed and designed by Riley Thai, and is maintained by the SDSS-V Data Visualization Team (Riley Thai, Brian Cherinka).
"""


@sl.component()
def HelpBlurb():
    """Dialog popup to provide general description of the application."""
    open, set_open = sl.use_state(False)

    with rv.AppBarNavIcon() as main:
        with sl.Tooltip("About the app"):
            sl.Button(
                icon_name="mdi-information-outline",
                icon=True,
                text=True,
                on_click=lambda: set_open(True),
            )
        with Dialog(open, ok=None, title="About", cancel="close"):
            with rv.Card(style_="width: 100%; height: 100%"):
                sl.Markdown(md_text)

    return main


@sl.component()
def ColumnGlossary():
    """Complete list of all columns and what they do"""
    df = State.df.value

    # don't use State.columns, instead get all natural columns
    columns = df.get_column_names(virtual=False)
    column_mdtext = "\n".join(columns)  # turn to markdown text

    # TODO: convert to markdown table of |Column | Description|

    # user-facing panel
    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=["Column Glossary"])
        with rv.ExpansionPanelContent():
            with sl.Column(gap="0px"):
                sl.Markdown(column_mdtext)

    return main
