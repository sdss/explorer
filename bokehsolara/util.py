from state import df
import vaex as vx


def check_categorical(expression: str | vx.Expression) -> bool:
    if isinstance(expression, str):
        expression: vx.Expression = df[expression]
    return (expression.dtype == "string") | (expression.dtype == "bool")
