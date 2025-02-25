from __future__ import print_function, division, absolute_import

# this is the config file for gunicorn + uvicorn, the ASGI gateway
# see https://www.uvicorn.org/ for uvicorn docs and
# https://docs.gunicorn.org/en/latest/settings.html for available gunicorn
# settings.
#
# run the following from the project terminal or set up a system service
# gunicorn -c wsgi_conf.py sdss_explorer.server.wsgi:app
import os

socket_dir = os.getenv("EXPLORER_SOCKET_DIR", "/tmp/explorer")
bind = [f"unix:{socket_dir}/explorer.sock", "0.0.0.0:8050"]
workers = os.getenv("EXPLORER_WORKERS", 4)
worker_class = "uvicorn.workers.UvicornWorker"
daemon = False
root_path = "/explorer"
timeout = 600
