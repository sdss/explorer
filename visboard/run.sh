#!/usr/bin/env bash

SOLARA_APP=scatter_demo.py uvicorn --workers 4 --host 0.0.0.0 --port 8765 solara.server.starlette:app
