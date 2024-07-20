#!/usr/bin/env bash

VAEX_CACHE="memory,disk" VAEX_CACHE_DISK_SIZE_LIMIT="10GB" VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB" solara run --theme-variant=dark --log-level=debug --log-level-uvicorn=info sdss_explorer.pages
