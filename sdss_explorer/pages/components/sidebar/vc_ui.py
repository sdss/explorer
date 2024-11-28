"""User-facing components for virtual columns"""

import solara as sl
import reacton.ipyvuetify as rv

from ...dataclass import Alert, VCList, SubsetState
from ..dialog import Dialog


def delete_column(key, VCData, df, name):
    """Deletes a virtual column from all 3 state objects"""
    #NOTE: order is important
    VCData.delete_column(name)
    df.delete_virtual_column(name)  # remove from df
    SubsetState.remove_virtual_column(
        key, name)  #  remove from column list, triggering updates in views


@sl.component()
def VirtualColumnCard(key, VCData, df, name: str, expression: str):
    """Card for individual virtual columns."""
    with rv.Card() as main:
        rv.CardTitle(children=[name])
        rv.CardSubtitle(children=[expression])
        with rv.CardActions(class_="justify-center"):
            sl.Button(
                label="",
                icon_name="mdi-delete-outline",
                text=True,
                icon=True,
                color="red",
                on_click=lambda: delete_column(key, VCData, df, name),
            )
    return main


@sl.component()
def VirtualColumnList(key, VCData, df):
    """Renders list of created virtual columns with delete buttons"""
    with sl.Column(gap="0px") as main:
        for name, expression in VCData.columns.value:
            VirtualColumnCard(key, VCData, df, name,
                              expression).key(key + name)

    return main


@sl.component()
def VirtualColumnsPanel(key: str):
    subset = SubsetState.subsets.value[key]
    VCData = sl.use_memo(lambda: VCList(subset),
                         dependencies=[])  # start new memoized instance
    df = subset.df
    open, set_open = sl.use_state(False)
    name, set_name = sl.use_state("snr_var_teff")
    expression, set_expression = sl.use_state("snr / e_teff**2")
    error, set_error = sl.use_state("")
    active = sl.use_reactive(False)

    def validate():
        """Function to ensure VC expression syntax is correct"""
        try:
            if expression == "" and name == "":
                return None
            # none cases
            assert name != "", "no name given"
            # check name
            assert name not in df.get_column_names(), "name already exists"

            # validate via AST
            assert expression != "", "no expression set"
            df.validate_expression(expression)

            assert df[
                expression].dtype != bool, "do not enter comparative expression"

            # alert user about powers
            if r"^" in expression:
                Alert.update(
                    "'^' is a bit operator. If you're looking to use powers, use '**' (Python syntax) instead.",
                    color="warning",
                )

            # set button to active
            active.set(True)
            return True

        except Exception as e:
            set_error(str(e))
            return False

    def add_column():
        """Adds virtual column"""
        df.add_virtual_column(name, expression)
        VCData.add_column(name, expression)
        SubsetState.add_virtual_column(key, name)
        close()

    result: sl.Result = sl.use_thread(validate,
                                      dependencies=[expression, name])

    def readd_virtual_columns():
        """On change of dataframe, readd all virtual columns."""
        for name, expression in VCData.columns.value:
            df.add_virtual_column(name, expression)
        return

    sl.use_thread(readd_virtual_columns, dependencies=[df])

    def close():
        """Clears state variables and closes dialog."""
        set_open(False)
        set_name("")
        set_expression("")
        active.set(False)

    with rv.ExpansionPanel() as main:
        rv.ExpansionPanelHeader(children=["Virtual Calculations"])
        with rv.ExpansionPanelContent():
            VirtualColumnList(key, VCData, df)
            with sl.Tooltip("Create custom columns based on the dataset"):
                sl.Button(
                    label="Add virtual column",
                    block=True,
                    on_click=lambda: set_open(True),
                )

        with Dialog(
                open,
                title="Add virtual column",
                on_cancel=close,
                ok="Add",
                close_on_ok=False,
                on_ok=add_column,
                persistent=True,
                ok_enable=active,
        ):
            sl.InputText(
                label="Enter an name for the new column.",
                value=name,
                on_value=set_name,
            )
            sl.InputText(
                label="Enter an expression for the new column.",
                value=expression,
                on_value=set_expression,
            )
            if result.state == sl.ResultState.FINISHED:
                if result.value:
                    sl.Success(
                        label="Valid expression & name entered.",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
                elif result.value is None:
                    sl.Info(
                        label="Enter an expression and a name for the column.",
                        icon=True,
                        dense=True,
                        outlined=False,
                    )
                else:
                    sl.Error(
                        label=f"Invalid expression/name entered: {error}",
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
