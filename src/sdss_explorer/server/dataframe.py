"""Interface with dataframe"""

import json
import logging
import os

import vaex as vx

from ..util.config import settings
from ..util.util import resolve_vastra

logger = logging.getLogger("server")


def load_mappings(release: str):
    """Loads release-aware mappings parquet with backward-compatible fallbacks."""
    release = (release or "dr19").lower()
    primary = os.path.join(settings.datapath, release, f"mappings_{release}.parquet")
    if os.path.exists(primary):
        return vx.open(primary)

    backup = os.path.join(settings.datapath, f"mappings_{release}.parquet")
    if os.path.exists(backup):
        return vx.open(backup)

    return vx.open(os.path.join(settings.datapath, "mappings.parquet"))


def load_columns(release: str, datatype: str, dataset: str):
    """Loads the given columns for a release and datatype"""
    vastra = resolve_vastra(release)
    with open(
        os.path.join(
            settings.datapath,
            release,
            f"columnsAll{datatype.capitalize()}-{vastra}.json",
        ),
        "r",
        encoding="utf-8",
    ) as f:
        columns = json.load(f)
    return columns[dataset]


def load_dataframe(
    release: str, datatype: str, dataset: str
) -> tuple[vx.DataFrame | None, list[str] | None]:
    """Loads base dataframe and applies dataset filter IMMEDIATELY to reduce memory usage"""
    dataroot_dir = settings.datapath
    if dataroot_dir:
        logger.debug("opening dataframe")
        vastra = resolve_vastra(release)
        cols = load_columns(release, datatype, dataset)
        # TODO: when we change the filegenerator, fix this here
        validCols = [
            col for col in cols if ("_flags" not in col) and (col != "pipeline")
        ]
        df = vx.open(
            os.path.join(
                dataroot_dir,
                release,
                f"explorerAll{datatype.capitalize()}-{vastra}.hdf5",
            )
        )
        dff = df[df[f"pipeline == '{dataset}'"]].extract()
        logger.debug("loaded dataframe!")
        return dff, validCols
    else:
        logger.critical("Cannot load df!")
        return None, None
