"""I/O functions for importing/exporting app state via JSON."""

import json
from copy import deepcopy
from typing import Any
from dataclasses import asdict

from ..dataclass.gridstate import GridData
from ..dataclass import Subset
from ..dataclass.vcdata import VCList

__all__ = ["export_subset", "export_layout", "export_vcdata"]


def export_subset(subset: Subset) -> dict[str, str | list[str]]:
    """Exports a given subset to JSON dict."""
    # NOTE: manually typed, otherwise asdict dumps entire df into memory
    data = dict(
        name=subset.name,
        expression=subset.expression,
        dataset=subset.dataset,
        carton=subset.carton,
        mapper=subset.mapper,
        flags=subset.flags,
    )
    return data


def export_layout(gridstate: GridData) -> dict[str, Any]:
    """Exports current grid layout to JSON dict."""
    # fetch layout and states
    layouts = deepcopy(gridstate.grid_layout.value)
    plotstates = gridstate.states.value

    # pop and convert plot state to dict.
    for layout in layouts:
        layout.pop("i")
    states = list()
    for state in plotstates:
        newstate = dict()
        for k, v in vars(state).items():
            if k == "Lookup":
                continue
            elif k == "plottype":
                newstate[k] = v
            else:
                newstate[k] = v.value
        states.append(newstate)

    return {"layout": layouts, "states": states}


def export_vcdata(vcdata: VCList) -> dict[str, str]:
    """Export the active Virtual Columns to a JSON dict."""
    return dict(vcdata.columns.value)
