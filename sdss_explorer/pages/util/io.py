"""I/O functions for importing/exporting app state via JSON."""

import json
from dataclasses import asdict

import reacton.ipyvuetify as rv

from ..dataclass.gridstate import GridData
from ..dataclass import Subset


def export_subset(subset: Subset) -> str:
    """Exports a given subset as JSON."""
    return json.dumps(asdict(subset))


#def export_layout(gridstate: GridData) -> str:
#    objects = [
#        x for x in gridstate.objects.value if not isinstance(x, rv.Card)
#    ]
#
#
#    return
