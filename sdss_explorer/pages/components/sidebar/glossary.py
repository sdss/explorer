"""Components to assist with user information, including about the app,"""

import os
import glob
import json
import solara as sl
from solara.alias import rv

from ...dataclass import _datapath
from ..dialog import Dialog
from solara.lab import Tabs, Tab

# TODO: maybe change to reference datapath in diff way to not use this try/except structure
try:
    with open(f"{_datapath()}/ipl3_partial.json") as f:
        data = json.load(f).values()
        f.close()
except Exception:
    data = None

# read help info
# NOTE: may not work on deployment, check with Brian.
HELPDIR = os.path.join(os.path.dirname(__file__), '../../../assets/help/')

# NOTE: the IO read on this is quite large, but it should be okay, right?
help_text = dict()
for file in map(os.path.basename, glob.glob(f'{HELPDIR}/*.md')):
    with open(f'{HELPDIR}/{file}', 'r') as f:
        icon = f.readline()
        help_text[file.split('.')[0].replace('_',
                                             ' ')] = (icon,
                                                      "\n".join(f.readlines()))
        f.close()

lookup = dict()
for i, k in enumerate(sorted(help_text.keys())):
    lookup[k] = i

print("LOOKUP", lookup)


class Help:
    """
    Help message settings
    """

    open = sl.reactive(False)
    tab = sl.reactive("")
    lookup = lookup

    @staticmethod
    def update(tab):
        Help.tab.set(Help.lookup[tab])
        Help.open.set(True)

    @staticmethod
    def close():
        Help.tab.set(1)
        Help.open.set(False)


@sl.component()
def HelpBlurb():
    """Dialog popup to provide short help blurbs for the application. Expected to read markdown files."""
    print("CURRENT TAB", Help.tab.value)
    with rv.AppBarNavIcon() as main:
        with sl.Tooltip("About the app + Help"):
            sl.Button(
                icon_name="mdi-information-outline",
                icon=True,
                text=True,
                on_click=lambda: Help.update('about'),
            )
        with Dialog(
                Help.open.value,
                ok=None,
                title="About",
                cancel="close",
                max_width='960',  # 1920/2
                on_cancel=lambda: Help.close(),
        ):
            with rv.Card(flat=True, style_="width: 100%; height: 100%"):
                with Tabs(value=Help.tab.value, on_value=Help.tab.set):
                    for label, (icon, text) in sorted(help_text.items()):
                        with Tab(label=label, icon_name=icon):
                            sl.Markdown(text)

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
