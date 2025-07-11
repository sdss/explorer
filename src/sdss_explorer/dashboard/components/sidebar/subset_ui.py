"""Main user-facing subset components"""

import logging
import solara as sl
import vaex as vx
import reacton.ipyvuetify as rv
from reacton.core import ValueElement

from ..dialog import Dialog

from ...dataclass import SubsetState, State, use_subset
from .subset_options import SubsetOptions

logger = logging.getLogger("dashboard")


@sl.component()
def SubsetMenu() -> ValueElement:
    """Control and display subset cards

    State variables:
        * `add`: whether the add dialog is open
        * `name`: the text input state of the name of new subset to be added
        * `model`: the open model, used to have first subset be open on initialize.
    """
    add = sl.use_reactive(False)
    name, set_name = sl.use_state("")  # new name of subset
    model, set_model = sl.use_state(0)

    def add_subset(name):
        "Wrapper on Subset Add to support dialog interface"
        if SubsetState.add_subset(name):
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
        with rv.ExpansionPanels(flat=True,
                                popout=True,
                                v_model=model,
                                on_v_model=set_model):
            for key in SubsetState.subsets.value.keys():
                logger.debug("rendering card" + str(key))
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
    """Holds filter update info, card structure, and calls to options.

    State variables:
        * `filter`: subset crossfilter hook
        * `open`: whether the panel is expanded or not

    Args:
        key: subset key

    Returns:
        main: SubsetCard element
    """
    subset = SubsetState.subsets.value[key]
    open, set_open = sl.use_state(False)
    df = subset.df
    if df is None:
        logger.debug(
            "we had a None df in SubsetCard, loading directly from State.")
        df = State.df.value

    filter, _set_filter = use_subset(id(df), key, "subset-summary")
    name = subset.name

    # progress bar logic
    if isinstance(filter, vx.Expression):
        # filter from plots or self
        dff = df[filter]
    else:
        # not filtered at all
        dff = df

    def get_lengths():
        logger.debug(key + ": promising length")
        length = df[df.pipeline == subset.dataset].count()[()]

        # BUG: this bypassses the AssertionError on chunks
        try:
            filtered_length_promise = dff.count(delay=True)
            logger.debug(key + ": promising length")
            dff.execute()
            filtered_length = filtered_length_promise.get()[()]
            logger.debug(key + ": length received = " + str(filtered_length))
        except AssertionError as e:
            from ...dataclass import Alert

            Alert.update(color="error", message="Failed to retrieve n rows!")
            filtered_length = 0

        return length, filtered_length

    length, filtered_length = sl.use_memo(get_lengths,
                                          dependencies=[dff, filter])

    print(length, filtered_length)
    not_filtered = filtered_length == length
    print(not_filtered)
    denom = max(length, 1)
    progress = filtered_length / denom * 100

    with rv.ExpansionPanel(v_model=open, on_v_model=set_open) as main:
        with rv.ExpansionPanelHeader():
            with sl.Row(gap="0px"):
                rv.Col(cols="4", children=[name])
                rv.Col(
                    cols="8",
                    class_="text--secondary",
                    children=[
                        rv.Icon(
                            children=["mdi-filter"],
                            style_="opacity:0.4" if not_filtered else "",
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
