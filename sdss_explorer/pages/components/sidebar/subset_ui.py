"""Main user-facing subset components"""

import solara as sl
import vaex as vx
import numpy as np
import reacton.ipyvuetify as rv
from solara.hooks.misc import use_force_update

from ..dialog import Dialog

from .subset_cards import SubsetState, updater_context


@vx.register_function()
def check_flags(flags, vals):
    """Converts flags & values to boolean vaex expression for use as a filter."""
    return np.any(np.logical_and(flags, vals), axis=1)


@sl.component()
def SubsetMenu():
    """Control and display subset cards"""
    add = sl.use_reactive(False)
    name, set_name = sl.use_state("")
    updater = use_force_update()
    updater_context.provide(updater)  # provide updater to context

    def add_subset(name):
        "Wraps subset add to support dialog interface"
        if SubsetState.add_subset(name):
            updater()  # force rerender
            close()

    def close():
        """Dialog close handler, resetting state vars"""
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
            print("Number of cards", len(SubsetState.cards.value))
            for card in SubsetState.cards.value:
                sl.display(card)
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
