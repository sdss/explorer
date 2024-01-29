#!/usr/bin/env bash

cd pages
solara run --theme-variant dark --workers 8 --production main.py
