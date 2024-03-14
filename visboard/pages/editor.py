from typing import cast
import re

import solara as sl
import numpy as np
import reacton.ipyvuetify as rv

from state import State


@sl.component
def SumCard():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "summary")
    # filter logic
    if filter:
        filtered = True
        dff = df[filter]
    else:
        filtered = False
        dff = df

    # title logic
    if filtered:
        title = "Filtered"
    else:
        title = "Showing all"
    progress = len(dff) / len(df) * 100

    with sl.Card(title=title, margin=0) as main:
        sl.ProgressLinear(value=progress, color="blue")
        with rv.CardText():
            if filtered:
                summary = f"{len(dff):,} / {len(df):,}"
            else:
                summary = f"{len(dff):,}"
            rv.Icon(
                children=["mdi-filter"],
                style_="opacity: 0.1" if not filtered else "",
            )
            rv.Html(tag="h3", children=[summary], style_="display: inline")


@sl.component
def ExprEditor():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-expression")
    dff = df
    if filter is not None:
        dff = dff[filter]
    expression, set_expression = sl.use_state("")
    error, set_error = sl.use_state(cast(str, None))

    def work():
        """
        Validates if the expression is valid, and returns
        a precise error message for any issues in the expression.
        """
        try:
            # TODO: this is hella spaghetti how fix
            if expression is None or expression == "":
                set_filter(None)
                return None
            # first, remove all spaces
            expr = expression.replace(" ", "")
            num_regex = r"^-?[0-9]+(?:\.[0-9]+)?(?:e-?\d+)?$"

            # get expression in parts, saving split via () regex
            subexpressions = re.split(r"(&|\||\)|\()", expr)
            n = 1
            cols = dff.get_column_names()
            for i, expr in enumerate(subexpressions):
                # saved regex info -> skip w/o enumerating
                if expr in ["", "&", "(", ")", "|"]:
                    continue

                parts = re.split(r"(>=|<=|<|>|==|!=)", expr)
                if len(parts) == 1:
                    assert False, f"expression {n} is invalid: no comparator"
                elif len(parts) == 5:
                    # first, check that parts 2 & 4 are lt or lte comparators
                    assert (
                        re.fullmatch(r"<=|<", parts[1]) is not None
                        and re.fullmatch(r"<=|<", parts[3]) is not None
                    ), f"expression {n} is invalid: not a proper 3-part inequality (a < col <= b)"

                    # check middle
                    assert (
                        parts[2] in dff.columns
                    ), f"expression {n} is invalid: must be comparing a data column (a < col <= b)"

                    # check a and b & if a < b
                    assert (
                        re.match(num_regex, parts[0]) is not None
                    ), f"expression {n} is invalid: must be numeric for numerical data column"
                    assert (
                        float(parts[0]) < float(parts[-1])
                    ), f"expression {n} is invalid: invalid inequality (a > b for a < col < b)"

                    # change the expression to valid format
                    subexpressions[i] = (
                        f"(({parts[0]}{parts[1]}{parts[2]})&({parts[2]}{parts[3]}{parts[4]}))"
                    )

                elif len(parts) == 3:
                    check = (parts[0] in dff.columns, parts[2] in dff.columns)
                    if np.any(check):
                        if check[0]:
                            col = parts[0]
                            num = parts[2]
                        elif check[1]:
                            col = parts[2]
                            num = parts[0]
                        dtype = str(dff[col].dtype)
                        if "float" in dtype or "int" in dtype:
                            assert (
                                re.match(num_regex, num) is not None
                            ), f"expression {n} is invalid: must be numeric for numerical data column"
                    else:
                        assert (
                            False
                        ), f"expression {n} is invalid: one part must be column"
                    assert (
                        re.match(r">=|<=|<|>|==|!=", parts[1]) is not None
                    ), f"expression {n} is invalid: middle is not comparator"

                    # change the expression in subexpression
                    subexpressions[i] = "(" + expr + ")"
                else:
                    assert False, f"expression {n} is invalid: too many comparators"

                # enumerate the expr counter
                n = n + 1

            # create expression as str
            expr = "(" + "".join(subexpressions) + ")"

            # query to see if it reduces to an unplottable length
            dfq = df[df[expr]]
            assert len(dfq) > 0, "expression reduces dataset to 0 rows"

            # set filter & exit
            set_filter(df[expr])
            return True

        except AssertionError as e:
            # INFO: it's probably better NOT to unset filters if assertions fail.
            # set_filter(None)
            set_error(e)  # saves error msg to state
            return False
        except SyntaxError as e:
            set_error("modifier at end of sequence with no expression")
            return False

    result: sl.Result[bool] = sl.use_thread(work, dependencies=[expression])

    with rv.ExpansionPanel() as main:
        with rv.ExpansionPanelHeader():
            rv.Icon(children=["mdi-function-variant"])
            with rv.CardTitle(children=["Expressions"]):
                pass
        with rv.ExpansionPanelContent():
            sl.InputText(label="Enter an expression",
                         value=expression,
                         on_value=set_expression)
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
