import os
from uuid import UUID
import numpy as np
import operator
from functools import reduce

from .dataframe import load_dataframe, mappings
from sdss_explorer.filter_functions import filter_carton_mapper, filter_flags

SCRATCH = os.getenv("EXPLORER_SCRATCH",
                    default="/home/riley/projects/sdss_dashboard/scratch")


def filter_dataframe(uuid: UUID, release: str, datatype: str, dataset: str,
                     **kwargs):
    """Filters dataframe based on public functions from Explorer"""
    dff = load_dataframe(release, datatype, dataset)
    filters = list()

    # generic
    combotype = kwargs.get("combotype", "AND")
    invert = kwargs.get("invert", False)

    # expression, etc
    expression = kwargs.get("expression", "")
    if expression:
        filters.append(dff[expression])

    carton = kwargs.get("carton", None)
    mapper = kwargs.get("mapper", None)
    flags = kwargs.get("flags", None)
    if carton:
        carton = carton.split(",")
    if mapper:
        mapper = mapper.split(",")
    if flags:
        flags = flags.split(",")
    if carton or mapper:
        cmp_filter = filter_carton_mapper(
            dff,
            mappings,
            combotype=combotype,
            invert=invert,
        )
        filters.append(cmp_filter)
    if flags:
        flagfilter = filter_flags(dff, dataset, invert=invert)
        filters.append(flagfilter)

    # concat all and go!
    if filters:
        totalfilter = reduce(operator.__and__, filters)
        dfe = dff[totalfilter].extract()
    else:
        dfe = dff

    # make directory and pass back after successful export
    os.makedirs(os.path.join(SCRATCH, str(uuid)), exist_ok=True)
    filepath = os.path.join(SCRATCH, str(uuid), "subsettest.parquet")
    dfe.export_parquet(filepath)
    return filepath


("aspcap", "apogeenet", "spall")[np.random.randint(0, 3)]
