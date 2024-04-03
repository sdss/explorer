#!/usr/bin/env bash

solara run --workers=8 --production --theme-variant=dark --host=0.0.0.0 --log-level-uvicorn=info sdss_explorer.pages
