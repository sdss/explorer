"""All filter conversion functions. Validation done in UI, but conversion to Expressions is done via these functions"""

import operator
import logging
import re
import numpy as np
import vaex as vx

# TODO: get dashboard or main depending on context of functions
logger = logging.getLogger("dashboard")

__all__ = [
    "check_flags", "filter_expression", "filter_carton_mapper", "filter_flags"
]


@vx.register_function(multiprocessing=True)
def check_flags(flags: vx.Expression, filters: vx.Expression) -> vx.Expression:
    """Converts flags & values to boolean vaex expression for use as a filter.

    Note:
        Registered as a `vaex.expression.Expression` method via the `register_function` decorator.

    Args:
        flags: bit flags expressions
        filters: which filters to apply
    Returns:
        Boolean expression of filters
    """
    return np.logical_and(flags, filters).any(axis=1)


operator_map = {"AND": operator.and_, "OR": operator.or_, "XOR": operator.xor}

flagList = {
    # TODO: more quick flags based on scientist input
    "sdss5 only": "release=='sdss5'",
    "snr > 50": "snr>=50",
    "purely non-flagged": "result_flags==0",
    #'no apo 1m': "telescope!='apo1m'", # WARNING: this one doesn't work for some reason, maybe it's not string; haven't checked
    "no bad flags": "flag_bad==0",
    "gmag < 17": "g_mag<=17",
}


def filter_expression(
    df: vx.DataFrame,
    columns: list[str],
    expression: str,
    invert: bool = False,
):
    """Converts expression to valid filter"""
    # first, remove all spaces
    expr = expression.replace(" ", "")
    logger.debug(f"expr: {expr}")
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
            ), (f"expression {n} is invalid: not a proper 3-part inequality (a < col <= b)"
                )

            # check middle
            assert parts[2] in columns, (
                f"expression {n} is invalid: must be comparing a data column (a < col <= b)"
            )

            # check a and b & if a < b
            assert re.match(num_regex, parts[0]) is not None, (
                f"expression {n} is invalid: must be numeric for numerical data column"
            )
            assert float(parts[0]) < float(parts[-1]), (
                f"expression {n} is invalid: invalid inequality (a > b for a < col < b)"
            )

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
                    assert re.match(num_regex, num) is not None, (
                        f"expression {n} is invalid: must be numeric for numerical data column"
                    )
            else:
                assert False, f"expression {n} is invalid: one part must be column"
            assert re.match(r">=|<=|<|>|==|!=", parts[1]) is not None, (
                f"expression {n} is invalid: middle is not comparator")

            # change the expression in subexpression
            subexpressions[i] = "(" + expr + ")"
        else:
            assert False, f"expression {n} is invalid: too many comparators"

        # enumerate the expr counter
        n = n + 1

    # create expression as str
    expr = "(" + "".join(subexpressions) + ")"
    logger.debug(f"expr final: {expr}")

    # set filter corresponding to inverts & exit
    if invert:  # NOTE: df will never be None unless something horrible happens
        logger.debug("inverting expression")
        return ~df[expr]
    else:
        return df[expr]


def filter_carton_mapper(
    df: vx.DataFrame,
    mapping: vx.DataFrame,
    carton: list[str],
    mapper: list[str],
    combotype: str = "AND",
    invert: bool = False,
) -> vx.Expression | None:
    """
    Filters a list of cartons and mappers

    Based on code written by Andy Casey for github.com/sdss/semaphore
    """
    if len(mapper) != 0 or len(carton) != 0:
        # mask
        if len(mapper) == 0:
            mask = mapping["alt_name"].isin(carton).values
        elif len(carton) == 0:
            mask = mapping["mapper"].isin(mapper).values
        else:
            mask = operator_map[combotype](
                mapping["mapper"].isin(mapper).values,
                mapping["alt_name"].isin(carton).values,
            )

        # determine active bits via mask and get flag_number & offset
        # NOTE: hardcoded nbits as 8, and nflags as 57
        bits = np.arange(len(mapping))[mask]
        num, offset = np.divmod(bits, 8)
        setbits = 57 > num  # ensure bits in flags

        # construct hashmap for each unique flag
        filters = np.zeros(57, dtype="uint8")
        unique_nums, indices = np.unique(num[setbits], return_inverse=True)
        for i, unique in enumerate(unique_nums):
            offsets = 1 << offset[setbits][indices == i]
            filters[unique] = np.bitwise_or.reduce(offsets)

        cmp_filter = df.func.check_flags(df["sdss5_target_flags"], filters)
    else:
        cmp_filter = None

    if invert and (cmp_filter is not None):
        logger.debug("inverting cmpfilter")
        return ~cmp_filter
    else:
        return cmp_filter


def filter_flags(df: vx.DataFrame,
                 flags: list[str],
                 dataset: str,
                 invert: bool = False) -> vx.Expression | None:
    """
    Generates a filter for flags
    """
    filters = []
    for flag in flags:
        # Skip iteration if the subset's dataset is 'best' and the flag is 'Purely non-flagged'
        if (dataset == "best") and (flag == "purely non-flagged"):
            continue
        # boss-only pipeline exceptions for zwarning_flags filtering
        elif np.isin(
                dataset,
            ("spall", "lineforest"),
        ) and (flag == "purely non-flagged"):
            filters.append("zwarning_flags!=0")
            continue
        filters.append(flagList[flag])

    # Determine the final concatenated filter
    if filters:
        # Join the filters with ")&(" and wrap them in outer parentheses
        concat_filter = f"(({')&('.join(filters)}))"
        concat_filter: vx.Expression = df[concat_filter]
        if invert and (concat_filter is not None):
            logger.debug("inverting flagfilter")
            concat_filter = ~concat_filter
    else:
        concat_filter = None
    return concat_filter
