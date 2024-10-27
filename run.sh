#!/usr/bin/env bash

EXPLORER_DEV=True VAEX_CACHE="memory,disk" VAEX_CACHE_DISK_SIZE_LIMIT="10GB" VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB" solara run --theme-variant=dark sdss_explorer.pages

#--log-level=debug --log-level-uvicorn=info
