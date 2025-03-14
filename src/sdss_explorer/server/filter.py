import os
import gc
import logging
from typing import ParamSpec
from uuid import UUID
import operator
from functools import reduce
from datetime import datetime

from .dataframe import load_dataframe, mappings
from ..util.config import settings
from ..util.filters import (
    filter_carton_mapper,
    filter_flags,
    filter_crossmatch,
    filter_expression,
)

_P = ParamSpec("_P")
logger = logging.getLogger("server")


def filter_dataframe(
    uuid: UUID,
    release: str,
    datatype: str,
    dataset: str,
    name: str = "A",
    expression: str = "",
    carton: str = "",
    mapper: str = "",
    flags: str = "",
    crossmatch: str = "",
    cmtype: str = "",
    combotype: str = "AND",
    invert: bool = False,
) -> None:
    """Filters and exports dataframe based on input subset parameters.

    Will write a file to the scratch disk based on `settings.scratch`.

    Args:
        uuid: unique job id
        release: data release
        datatype: datatype (star or visit)
        dataset: specific dataset i.e. aspcap, spall, best
        name: name of subset, used in generating output file
        expression: filter expression
        carton: comma-separated cartons
        mapper: comma-separated mappers
        flags: comma-separated flagss
        combotype: logical reducer for carton/mapper
        invert: whether to invert all filters

    Returns:
        None
    """
    logger.debug("starting filter job")
    dff, columns = load_dataframe(release, datatype, dataset)
    if (dff is None) or (columns is None):
        raise Exception("dataframe/columns load failed")
    filters = list()

    # generic unpack; show to console
    logger.debug(f"""requested {release}/{datatype}/{dataset}{uuid}
                 expr:                 {expression} 
                 carton:               {carton} 
                 mapper:               {mapper} 
                 flags:                {flags}
                 crossmatch({cmtype}): {crossmatch[:8]}...
                 combotype:            {combotype}
                 invert:               {invert}
                 """)

    # process list-like data
    if carton:
        carton: list[str] = carton.split(",")
    if mapper:
        mapper: list[str] = mapper.split(",")
    if flags:
        flags: list[str] = flags.split(",")

    # make all filters via utility funcs
    if expression:
        filters.append(
            filter_expression(dff, columns, expression, invert=invert))
    if carton or mapper:
        cmp_filter = filter_carton_mapper(
            dff,
            mappings,
            carton if carton else [],
            mapper if mapper else [],
            combotype=combotype,
            invert=invert,
        )
        filters.append(cmp_filter)
    if flags:
        flagfilter = filter_flags(dff, flags, dataset, invert=invert)
        filters.append(flagfilter)
    if len(crossmatch) > 0:
        crossmatchFilter = filter_crossmatch(dff, crossmatch, cmtype)
        filters.append(crossmatchFilter)

    # concat all and go!
    filters = [f for f in filters if f is not None]
    if filters:
        totalfilter = reduce(operator.__and__, filters)
        dff = dff[totalfilter]
    if len(dff) == 0:
        raise Exception("attempting to export 0 length df")

    # make directory and pass back after successful export
    os.makedirs(os.path.join(settings.scratch, str(uuid)), exist_ok=True)
    currentTime = "{date:%Y-%m-%d_%H:%M:%S}".format(date=datetime.now())
    filename = f"subset-{name}-{release}-{datatype}-{dataset}-{currentTime}.parquet"
    filepath = os.path.join(str(uuid), filename)
    disk_path = os.path.join(settings.scratch, filepath)

    # extract, then export
    dff = dff[columns].extract()
    dff.export_parquet(disk_path, chunk_size=int(60e3))

    # cleanup to free memory slightly
    dff.close()
    del dff
    gc.collect()
    logger.debug("completed filter job, exiting now!")
    return filepath
