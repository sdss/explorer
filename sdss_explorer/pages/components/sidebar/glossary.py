"""Components to assist with user information, including about the app,"""

import os
import glob
import solara as sl
from solara.alias import rv
import numpy as np

from ...dataclass import State
from ..dialog import Dialog
from ...util import filter_regex
from ..textfield import InputTextExposed
from solara.lab import Tabs, Tab

# read help info
# TODO: consider moving to State? idk
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
    # TODO: fetch via valis instead of via precompiled json
    # TODO: make datamodel/airflow render for data file
    dm = State.datamodel.value
    query, set_query = sl.use_state("")
    filter, set_filter = sl.use_state(None)
    dmf = dm
    if filter is not None:
        dmf = dm[filter]

    def update_columns():
        # always need to cut
        if query:
            # union of regex across name and desc
            alpha = filter_regex(dm, query=query, col='name')
            beta = filter_regex(dm, query=query, col='description')
            set_filter(np.logical_or(alpha, beta))

        elif query == "":
            set_filter(None)

    result = sl.use_thread(update_columns, dependencies=[query])

    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=["Column Glossary"])
        with rv.ExpansionPanelContent():
            with sl.Div():
                if dm is None:
                    sl.Error("Error in datamodel load.")
                else:
                    InputTextExposed(
                        label="Filter columns by name",
                        value=query,
                        on_value=set_query,
                        continuous_update=True,
                    )
                    with sl.GridFixed(columns=1,
                                      align_items="end",
                                      justify_items="stretch"):
                        if result.state == sl.ResultState.FINISHED:
                            if len(dmf) == 0:
                                sl.Warning(
                                    "No columns found, try a different filter")
                            else:
                                # summary text logic
                                if len(dmf) > 20:
                                    summary = f"{len(dmf):,}/{len(dm):,} columns (showing 20)"
                                elif len(dmf) == len(dm):
                                    summary = (
                                        f"{len(dm):,} total columns (showing 20)"
                                    )
                                else:
                                    summary = f"{len(dmf):,}/{len(dm):,} columns"

                                sl.Info(summary)
                                # TODO: change from showing just first 20 to more via lazy-loading
                                for n, d in enumerate(dmf.iloc):
                                    if n > 19:
                                        break
                                    with sl.Columns([1, 1]):
                                        sl.Text(d['name'])
                                        sl.Text(d['description'])

                        else:
                            with sl.Div():
                                sl.Text("Loading...")
                                rv.ProgressCircular(indeterminate=True,
                                                    class_="solara-progress")
    return main
