import os
from uuid import UUID
import operator
from functools import reduce
from datetime import datetime

from .dataframe import load_dataframe, mappings
from sdss_explorer.filter_functions import (
    filter_carton_mapper,
    filter_flags,
    filter_expression,
)

SCRATCH = os.getenv("EXPLORER_SCRATCH", default="./scratch")


def filter_dataframe(uuid: UUID, release: str, datatype: str, dataset: str,
                     **kwargs):
    """Filters dataframe based on public functions from Explorer"""
    dff, columns = load_dataframe(release, datatype, dataset)
    if (dff is None) or (columns is None):
        raise Exception("dataframe/columns oad failed")
    filters = list()

    name = kwargs.get("name", "A")

    # generic
    combotype = kwargs.get("combotype", "AND")
    invert = kwargs.get("invert", False)

    # expression, etc
    expression = kwargs.get("expression", "")
    if expression:
        filters.append(
            filter_expression(dff, columns, expression, invert=invert))

    # process list-like data
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
            carton,
            mapper,
            combotype=combotype,
            invert=invert,
        )
        filters.append(cmp_filter)
    if flags:
        flagfilter = filter_flags(dff, flags, dataset, invert=invert)
        filters.append(flagfilter)

    # concat all and go!
    if filters:
        totalfilter = reduce(operator.__and__,
                             [f for f in filters if f is not None])
        dfe = dff[totalfilter]
    else:
        dfe = dff
    dfe = dfe[columns].extract()
    if len(dfe) == 0:
        print(uuid)
        print(dataset, datatype)
        print(carton, mapper)
        print([filter.__str__() for filter in filters])
        raise Exception("attempting to export 0 rows")

    # make directory and pass back after successful export
    os.makedirs(os.path.join(SCRATCH, str(uuid)), exist_ok=True)
    currentTime = "{date:%Y-%m-%d_%H:%M:%S}".format(date=datetime.now())
    filepath = os.path.join(SCRATCH, str(uuid),
                            f"subset-{name}-{currentTime}.parquet")
    dfe.export_parquet(filepath)
    return filepath
