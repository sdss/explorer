"""Main user-facing subset components"""

from typing import List, Union, Tuple
import solara as sl
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv
from solara.hooks.misc import use_force_update
from reacton.core import ValueElement

from ..dialog import Dialog

from ...dataclass import SubsetState, State, use_subset
from .subset_options import updater_context, SubsetOptions


@vx.register_function(multiprocessing=True)
def check_flags(flags: vx.Expression, filters: vx.Expression):
    """Converts flags & values to boolean vaex expression for use as a filter."""
    return np.logical_and(flags, filters).any(axis=1)


@sl.component()
def SubsetMenu() -> ValueElement:
    """Control and display subset cards"""
    add = sl.use_reactive(False)
    name, set_name = sl.use_state("")
    updater = use_force_update()
    updater_context.provide(updater)  # provide updater to context

    def add_subset(name):
        "Wrapper on Subset Add to support dialog interface"
        if SubsetState.add_subset(name):
            updater()  # force rerender
            close()

    def close():
        """Dialog close handler; resets state variables."""
        add.set(False)
        set_name("")
        return

    with sl.Column(gap="0px") as main:
        with rv.Card(class_="justify-center",
                     flat=True,
                     style_="width: 100%; height: 100%"):
            rv.CardTitle(
                class_="justify-center",
                children=["Subsets"],
            )
            with rv.CardText():
                with sl.Tooltip("Create filtered subsets of the dataset"):
                    sl.Button(
                        label="Add new subset",
                        on_click=lambda: add.set(True),
                        block=True,
                    )
        # NOTE: starting app with expanded panels requires
        # enabling the multiple prop for this version of vuetify.
        # This is really annoying for UX (too much info), so we cant do it
        with rv.ExpansionPanels(flat=True, popout=True):
            # multiple=True,
            # v_model=model,
            # on_v_model=set_model):
            for key in SubsetState.subsets.value.keys():
                SubsetCard(key).key(key)
        with Dialog(
                add,
                title="Enter a name for the new subset",
                close_on_ok=False,
                on_ok=lambda: add_subset(name),
                on_cancel=lambda: set_name(""),
        ):
            sl.InputText(
                label="Subset name",
                value=name,
                on_value=set_name,
            )

    return main


@sl.component()
def SubsetCard(key: str) -> ValueElement:
    """Holds filter update info, card structure, and calls to options"""
    subset = SubsetState.subsets.value[key]
    df = subset.df
    if df is None:
        df = State.df.value
    filter, _set_filter = use_subset(id(df), key, "subset-summary")
    name = subset.name
    dataset = subset.dataset
    print("------STATE------")
    print(State)
    print("------SUBSET------")
    print(subset)

    # progress bar logic
    if isinstance(filter, vx.Expression):
        # filter from plots or self
        dff = df[filter]
    else:
        # not filtered at all
        dff = df

    def check(a, b):
        return a < b

    length = df.count()[()]
    filtered_length = dff.count()[()]

    filtered = filtered_length < length
    denom = max(length, 1)
    progress = filtered_length / denom * 100

    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            with sl.Row(gap="0px"):
                rv.Col(cols="4", children=[name])
                rv.Col(
                    cols="8",
                    class_="text--secondary",
                    children=[
                        rv.Icon(
                            children=["mdi-filter"],
                            style_="opacity:e0.1" if not filtered else "",
                        ),
                        f"{filtered_length:,}",
                    ],
                )

        with rv.ExpansionPanelContent():
            # filter bar
            with sl.Column(gap="12px"):
                sl.ProgressLinear(value=progress, color="blue")
                SubsetOptions(key, lambda: SubsetState.remove_subset(key))
    return main
