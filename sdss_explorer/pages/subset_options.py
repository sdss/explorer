"""Subset options menu sub-components, including expression editor, carton/mapper menu, and more (to be added)"""

import solara as sl
import reacton.ipyvuetify as rv

from .state import State


@sl.component
def ExprEditor(expression, set_expression, error, result):
    """Expression editor user-facing set"""
    # expression editor
    with sl.Column(gap="0px") as main:
        sl.InputText(
            label="Enter an expression",
            value=expression,
            on_value=set_expression,
        )
        if result.state == sl.ResultState.FINISHED:
            if result.value:
                sl.Success(
                    label="Valid expression entered.",
                    icon=True,
                    dense=True,
                    outlined=False,
                )
            elif result.value is None:
                sl.Info(
                    label="No expression entered. Filter unset.",
                    icon=True,
                    dense=True,
                    outlined=False,
                )
            else:
                sl.Error(
                    label=f"Invalid expression entered: {error}",
                    icon=True,
                    dense=True,
                    outlined=False,
                )

        elif result.state == sl.ResultState.ERROR:
            sl.Error(f"Error occurred: {result.error}")
        else:
            sl.Info("Evaluating expression...")
            rv.ProgressLinear(indeterminate=True)
    return main


def CartonMapperPanel(mapper, set_mapper, carton, set_carton, dataset,
                      set_dataset):
    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=["Targeting filters"])
        with rv.ExpansionPanelContent():
            with sl.Column(gap="2px"):
                with sl.Columns([1, 1]):
                    sl.SelectMultiple(
                        label="Mapper",
                        values=mapper,
                        on_value=set_mapper,
                        dense=True,
                        all_values=State.mapping.value["mapper"].unique(),
                        classes=['variant="solo"'],
                    )
                    sl.SelectMultiple(
                        label="Dataset",
                        values=dataset,
                        on_value=set_dataset,
                        dense=True,
                        # TODO: fetch via valis or via df itself
                        all_values=["apogeenet", "thecannon", "aspcap"],
                        classes=['variant="solo"'],
                    )
                sl.SelectMultiple(
                    label="Carton",
                    values=carton,
                    on_value=set_carton,
                    dense=True,
                    all_values=State.mapping.value["alt_name"].unique(),
                    classes=['variant="solo"'],
                )
    return main
