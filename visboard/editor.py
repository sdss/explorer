from typing import cast

import solara as sl
import reacton.ipyvuetify as rv

from state import State


@sl.component()
def SumCard():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "summary")

    dff = df
    filtered = False
    if filter is not None:
        filtered = True
        dff = df[filter]
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


@sl.component()
def ExprEditor():
    df = State.df.value
    filter, set_filter = sl.use_cross_filter(id(df), "filter-expression")
    dff = df
    if filter is not None:
        dff = dff[filter]
    expression, set_expression = sl.use_state(cast(str, None))
    print("expreditor:fullrerun")

    def work():
        print("expreditor:rerun")
        try:
            # TODO: this is hella spaghetti how fix
            if expression is None or expression == "":
                print("expreditor:empty")
                set_filter(None)
                return None
            modifiers = [">", "<", "=", "!"]
            assert any(modifier in expression for modifier in modifiers)

            # get expression in parts
            exprlist = []
            for modifier in modifiers:
                exprs = expression.split("&")
                for expr in exprs:
                    expr = expr.split(modifier)
                    if len(expr) == 2 or len(expr) == 3:
                        exprlist.append(expr)
                        if len(exprs) == 1:
                            break
            if "&" in expression:
                assert all(b in expression for b in ["(", ")"])

            for expr in exprlist:
                if len(expr) == 2:
                    assert (expr[0].strip().replace(")", "").replace("(", "")
                            in dff.get_column_names())
                    assert expr[-1].strip().replace(")", "").replace("(",
                                                                     "") != ""
                else:
                    print("expreditor:3part")
                    assert (expr[1].strip().replace(")", "").replace("(", "")
                            in dff.get_column_names())
                    assert expr[-1].strip().replace(")", "").replace("(",
                                                                     "") != ""
                    assert expr[0].strip().replace(")", "").replace("(",
                                                                    "") != ""
            import numpy as np

            assert np.count_nonzero(df["(" + expression + ")"].evaluate()) > 0

            # pass all checks, then set the filter
            set_filter(df["(" + expression + ")"])
            print("expreditor:valid")
            return True

        except AssertionError:
            set_filter(None)
            print("expreditor:invalid")
            return False

    result: sl.Result[bool] = sl.use_thread(work, dependencies=[expression])

    with sl.Card(margin=0) as main:
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
                    label="Invalid expression entered.",
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
