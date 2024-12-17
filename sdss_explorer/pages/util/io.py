"""I/O functions for importing/exporting app state via JSON."""

import json
from copy import deepcopy
from typing import Any
from dataclasses import asdict

from ..dataclass.gridstate import GridData
from ..dataclass import Subset

__all__ = [
    'import_grid_layout', 'import_subset', 'export_subset', 'export_layout'
]


def import_subset(subset_json: str) -> dict:
    """Convert imported subset JSON to Subset keyword arguments"""
    # convert json to dict for kwargs
    return json.loads(subset_json)


def import_grid_layout(layout_json: str) -> GridData:
    """Convert imported layout JSON to GridData"""
    pass


def export_subset(subset: Subset) -> str:
    """Exports a given subset to JSON str."""
    return asdict(subset)


def export_layout(gridstate: GridData) -> dict[str, Any]:
    """Exports current grid layout to JSON str."""
    # fetch layout and states
    layouts = deepcopy(gridstate.grid_layout.value)
    plotstates = gridstate.states.value

    # pop and convert plot state to dict.
    for layout in layouts:
        layout.pop('i')
    states = list()
    for state in plotstates:
        newstate = dict()
        for k, v in vars(state).items():
            if (k == 'Lookup'):
                continue
            elif (k == 'plottype'):
                newstate[k] = v
            else:
                newstate[k] = v.value
        states.append(newstate)

    return {'layout': layouts, 'states': states}
