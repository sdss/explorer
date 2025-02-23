"""Interface with dataframe"""

import json
import os
import logging
import vaex as vx

EXPLORER_DATAPATH = os.getenv(
    "EXPLORER_DATAPATH",
    default="/home/riley/projects/explorer/data/")  # TODO: set default none
VASTRA = str(os.getenv("VASTRA", default="0.6.0"))

logger = logging.getLogger("explorerdownload")

if EXPLORER_DATAPATH is None:
    logger.critical("DOWNLOAD API CANNOT FIND DATAPATH")
    raise


def get_datapath():
    return EXPLORER_DATAPATH


mappings = vx.open(os.path.join(get_datapath(), "mappings.parquet"))


def load_columns(release: str, datatype: str, dataset: str):
    """Loads the given columns for a release and datatype"""
    with open(
            os.path.join(
                EXPLORER_DATAPATH,
                release,
                f"columnsAll{datatype.capitalize()}-{VASTRA}.json",
            )) as f:
        columns = json.load(f)
    return columns[dataset]


def load_dataframe(
        release: str, datatype: str,
        dataset: str) -> tuple[vx.DataFrame | None, list[str] | None]:
    """Loads base dataframe and applies dataset filter IMMEDIATELY to reduce memory usage"""
    dataroot_dir = get_datapath()
    if dataroot_dir:
        logger.info("opening dataframe")
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
                f"explorerAll{datatype.capitalize()}-{VASTRA}.hdf5",
            ))
        dff = df[df[f"pipeline == '{dataset}'"]].extract()
        logger.info("loaded dataframe!")
        return dff, validCols
    else:
        logger.critical("Cannot load df!")
        return None, None
