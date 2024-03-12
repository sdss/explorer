#!/usr/bin/env bash

cd pages
solara run --workers 8 --production main.py
