#!/usr/bin/env bash

SOLARA_THEME_SHOW_BANNER=False VAEX_CACHE="memory,disk" VAEX_CACHE_DISK_SIZE_LIMIT="10GB" VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB" solara run --workers=1 --production --theme-variant=dark --host=0.0.0.0 --log-level-uvicorn=info sdss_explorer.pages
