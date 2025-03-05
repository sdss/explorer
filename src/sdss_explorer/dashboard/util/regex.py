"""Regex functions with Alerts"""

import re
from itertools import permutations
from typing import List, Optional

import vaex as vx
import pandas as pd
from ..dataclass import Alert

__all__ = ["gen_fuzzy_regex", "filter_regex"]


def gen_fuzzy_regex(input_string: str) -> str:
    """Generate a basic fuzzy finding regex pattern from a string.

    A string could be "a foo bar" and the pattern would become:
    ((a).*(foo).*(bar))|((a).*(bar).*(foo))|((foo).*(a).*(bar))|...

    :param input_string: the input string to generate the pattern from
    :return: the generated pattern as a string
    """
    # escape special characters and filter the words for 0 length
    words = [re.escape(word) for word in input_string.split() if word]
    words.sort(key=len)  # sort for short matches first

    # search all permuatations
    word_permutations = permutations(words)
    patterns = []
    for perm in word_permutations:
        pattern_part = ".*".join(f"(?i)({word})" for word in perm)
        patterns.append(f"({pattern_part})")

    return "|".join(patterns)


def filter_regex(data: vx.DataFrame | pd.DataFrame | List,
                 query: str,
                 col: Optional[str] = None):
    """Filter a dataframe or list by a column for a given query"""
    try:
        if len(query) == 0:
            return []
        else:
            if isinstance(data, vx.DataFrame) or isinstance(
                    data, pd.DataFrame):
                return data[col].str.contains(gen_fuzzy_regex(query),
                                              regex=True)
            # regex a list
            elif isinstance(data, list):
                return list(
                    filter(re.compile(gen_fuzzy_regex(query)).search, data))
    except Exception:
        Alert.update(
            message=
            "Filter on autocomplete crashed! If persistent, please inform server admins.",
            color="error",
        )
        return []
