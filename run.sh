#!/usr/bin/env bash

SOLARA_CHECK_HOOKS=off SOLARA_KERNEL_CULL_TIMEOUT=1m SOLARA_THEME_SHOW_BANNER=False EXPLORER_DEV=True VAEX_CACHE="memory,disk" VAEX_CACHE_DISK_SIZE_LIMIT="10GB" VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB" solara run --theme-variant=dark sdss_explorer.pages --workers=1
