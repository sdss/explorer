import operator
import re
from functools import reduce
from typing import cast

import numpy as np
import reacton.ipyvuetify as rv
import solara as sl
from reacton.core import ValueElement

from state import df
from textfield import InputTextExposed


def ExprEditor() -> ValueElement:
    """Expression editor."""
    # state for expreditor

    _, set_expfilter = sl.use_cross_filter(id(df), name="editor")
    expression, set_expression = sl.use_state("")

    open, set_open = sl.use_state(False)
    error, set_error = sl.use_state(cast(str, None))

    # Expression Editor thread
    def update_expr():
        """
        Validates if the expression is valid, and returns
        a precise error message for any issues in the expression.
        """
        columns = df.get_column_names()
        try:
            if expression is None or expression == "" or expression == "None":
                set_expfilter(None)
                set_expression("")
                return None
            # first, remove all spaces
            expr = expression.replace(" ", "")
            num_regex = r"^-?[0-9]+(?:\.[0-9]+)?(?:e-?\d+)?$"

            # get expression in parts, saving split via () regex
            subexpressions = re.split(r"(&|\||\)|\()", expr)
            n = 1
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
                        parts[2] in columns
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
                    check = (parts[0] in columns, parts[2] in columns)
                    if np.any(check):
                        if check[0]:
                            col = parts[0]
                            num = parts[2]
                        elif check[1]:
                            col = parts[2]
                            num = parts[0]
                        dtype = str(df[col].dtype)
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
            print(expr)

            # set filter corresponding to inverts & exit
            set_expfilter(df[expr])
            return True

        except AssertionError as e:
            # INFO: it's probably better NOT to unset filters if assertions fail.
            # set_filter(None)
            set_error(e)  # saves error msg to state
            return False
        except SyntaxError:
            set_error("modifier at end of sequence with no expression")
            return False

    result: sl.Result[bool] = sl.use_thread(update_expr,
                                            dependencies=[expression])
    if result.state == sl.ResultState.FINISHED:
        if result.value:
            errorFound = False
            message = "Valid expression entered"
        elif result.value is None:
            errorFound = False
            message = "No expression entered. Filter unset."
        else:
            errorFound = True
            message = f"Invalid expression entered: {error}"

    elif result.state == sl.ResultState.ERROR:
        errorFound = True
        message = f"Backend failure occurred: {result.error}"
    else:
        # processing
        errorFound = False
        message = None

    # expression editor
    with sl.Column(gap="0px") as main:
        with sl.Row(justify="center", style={"align-items": "center"}):
            InputTextExposed(
                label="Enter an expression",
                value=expression,
                on_value=set_expression,
                message=message,
                error=errorFound,
                clearable=True,
                placeholder="teff < 15e3 & (mg_h > -1 | fe_h < -2)",
            )
    return main
