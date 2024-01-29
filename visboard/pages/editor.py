from typing import cast

import solara as sl
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
            rv.Icon(children=["mdi-filter"],
                    style_="opacity: 0.1" if not filtered else "")
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

    def reset():
        set_expression("")
        set_error(cast(str, None))

    # INFO: resets on dataframe change
    sl.use_thread(reset, dependencies=[State.df.value])

    def work():
        try:
            # TODO: this is hella spaghetti how fix
            if expression is None or expression == "":
                set_filter(None)
                return None
            modifiers = [">=", "<=", "!=", ">", "<", "=="]
            assert any(modifier in expression for modifier in
                       modifiers), "expression requires comparative modifier"

            # get expression in parts
            exprlist = []
            for modifier in modifiers:
                exprs = expression.split("&")
                for expr in exprs:
                    expr = expr.split(modifier)
                    if len(expr) == 2 or len(expr) == 3:
                        expr.append(modifier)
                        exprlist.append(expr)
                        if len(exprs) == 1:
                            break

            completed_expression = []
            for expr in exprlist:
                if len(expr) == 3:
                    mod = expr[-1].strip().replace(")", "").replace("(", "")
                    if (expr[0].strip().replace(")", "").replace("(", "")
                            in dff.get_column_names()):
                        col = expr[0].strip().replace(")", "").replace("(", "")
                        num = expr[1].strip().replace(")", "").replace("(", "")
                    elif (expr[1].strip().replace(")", "").replace("(", "")
                          in dff.get_column_names()):
                        col = expr[1].strip().replace(")", "").replace("(", "")
                        num = expr[0].strip().replace(")", "").replace("(", "")
                    else:
                        assert False, "one part must be a data column"
                    completed_expression.append(f"({col}{mod}{num})")
                else:
                    assert (
                        expr[1].strip().replace(")", "").replace("(", "")
                        in dff.get_column_names()), "middle must be a column"

                    assert (expr[0].strip().replace(")", "").replace("(", "")
                            != ""), "ends must be numeric"
                    assert (expr[2].strip().replace(")", "").replace("(", "")
                            != ""), "ends must be numeric"
                    col = expr[1].strip().replace(")", "").replace("(", "")
                    low = expr[0].strip().replace(")", "").replace("(", "")
                    high = expr[2].strip().replace(")", "").replace("(", "")
                    completed_expression.append(
                        f"(({col} > {low}) & ({col} < {high}))")
            import numpy as np

            completed_expression = " & ".join(completed_expression)

            assert (np.count_nonzero(df["(" + completed_expression +
                                        ")"].evaluate())
                    > 10), "expression too precise (results in length < 10)"
            # pass all checks, then set the filter
            set_filter(df["(" + completed_expression + ")"])
            return True

        except AssertionError as e:
            set_filter(None)
            set_error(e)
            return False

    result: sl.Result[bool] = sl.use_thread(work, dependencies=[expression])

    with sl.Card(title="Expression editor", margin=0) as main:
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
