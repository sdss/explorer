"""Components to assist with user information, including about the app,"""

import json
import solara as sl
from solara.alias import rv

from ...dataclass import _datapath
from ..dialog import Dialog

# TODO: maybe change to reference datapath in diff way to not use this try/except structure
try:
    with open(f"{_datapath()}/ipl3_partial.json") as f:
        data = json.load(f).values()
        f.close()
except:
    data = None

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
        with Dialog(
                open,
                ok=None,
                title="About",
                cancel="close",
                on_cancel=lambda: set_open(False),
        ):
            with rv.Card(flat=True, style_="width: 100%; height: 100%"):
                sl.Markdown(md_text)

    return main


@sl.component()
def ColumnGlossary():
    """Complete list of all columns and what they do"""
    # TODO: fetch via valis instead of via basic
    # TODO: for above, make datamodel/airflow render for data file
    json = data
    filter, set_filter = sl.use_state("")
    columns, set_columns = sl.use_state(json)

    def update_columns():
        if filter:
            set_columns(
                [k for k in json if filter.lower() in k["name"].lower()])
        elif filter == "":
            set_columns(data)

    result = sl.use_thread(update_columns, dependencies=[filter])

    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=["Column Glossary"])
        with rv.ExpansionPanelContent():
            with sl.Div():
                if data is None:
                    sl.Error("Error in datamodel load.")
                else:
                    sl.InputText(
                        label="Filter columns by name",
                        value=filter,
                        on_value=set_filter,
                        continuous_update=True,
                    )
                    with sl.GridFixed(columns=1,
                                      align_items="end",
                                      justify_items="stretch"):
                        if result.state == sl.ResultState.FINISHED:
                            if len(columns) == 0:
                                sl.Warning(
                                    "No columns found, try a different filter")
                            else:
                                # summary text logic
                                if len(columns) > 20:
                                    summary = f"{len(columns):,}/{len(data):,} columns (showing 20)"
                                elif len(columns) == len(data):
                                    summary = (
                                        f"{len(data):,} total columns (showing 20)"
                                    )
                                else:
                                    summary = f"{len(columns):,}/{len(data):,} columns"

                                sl.Info(summary)
                                # TODO: change from showing just first 20 to more via lazy-loading
                                for n, col in enumerate(columns):
                                    if n > 20:
                                        break
                                    name = col["name"]
                                    desc = col["description"]
                                    with sl.Columns([1, 1]):
                                        sl.Text(name)
                                        sl.Text(desc, style={"opacity": ".5"})
                        else:
                            with sl.Div():
                                sl.Text("Loading...")
                                rv.ProgressCircular(indeterminate=True,
                                                    class_="solara-progress")
    return main
