"""Interface with dataframe"""

import json
import os
import logging
import vaex as vx

from .config import settings

logger = logging.getLogger("server")

if settings.datapath is None:
    logger.critical("SERVER CANNOT FIND DATAPATH")
    raise

mappings = vx.open(os.path.join(settings.datapath, "mappings.parquet"))


def load_columns(release: str, datatype: str, dataset: str):
    """Loads the given columns for a release and datatype"""
    with open(
            os.path.join(
                settings.datapath,
                release,
                f"columnsAll{datatype.capitalize()}-{settings.vastra}.json",
            )) as f:
        columns = json.load(f)
    return columns[dataset]


def load_dataframe(
        release: str, datatype: str,
        dataset: str) -> tuple[vx.DataFrame | None, list[str] | None]:
    """Loads base dataframe and applies dataset filter IMMEDIATELY to reduce memory usage"""
    dataroot_dir = settings.datapath
    if dataroot_dir:
        logger.debug("opening dataframe")
        cols = load_columns(release, datatype, dataset)
        # TODO: when we change the filegenerator, fix this here
        validCols = [
            col for col in cols
            if ("_flags" not in col) and (col != "pipeline")
        ]
        df = vx.open(
            os.path.join(
                dataroot_dir,
                release,
                f"explorerAll{datatype.capitalize()}-{settings.vastra}.hdf5",
            ))
        dff = df[df[f"pipeline == '{dataset}'"]].extract()
        logger.debug("loaded dataframe!")
        return dff, validCols
    else:
        logger.critical("Cannot load df!")
        return None, None
