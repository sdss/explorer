import vaex as vx  # noqa


def check_catagorical(expression):
    return expression.dtype == "string"
