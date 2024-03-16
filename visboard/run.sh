#!/usr/bin/env bash

export EXPLORER_PATH=/home/riley/Projects/visboard/data
cd pages
solara run --workers 8 main.py
