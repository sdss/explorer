# Explorer
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![Versions](https://img.shields.io/badge/python-3.10-blue)

The SDSS Parameter Explorer is a custom data visualization application developed for SDSS-V's Data Release 19, built using `FastAPI`, `solara`, `plotly` and `vaex`. It is designed to specifically interface with custom SDSS datafiles, providing filtered access, statistics, and visualization to the parameter data products from SDSS-V.

## Components

Explorer ships with two components
- `sdss_explorer.dashboard` :: main dashboard app, available [online](data.sdss5.org/zora).
- `sdss_explorer.server` :: a FastAPI backend for serving custom dataset renders.

## Installation

To just install it tracking `main`, run:
```
pip install git+https://www.github.com/sdss/explorer.git@main
```

or, to have a local copy on your machine, clone and install as an editable package via `pip`:
```
git clone https://www.github.com/sdss/explorer.git ./sdss-explorer
cd sdss-explorer
pip install -e . 
```

These instructions are the same as in `conda`.

## Development

We recommend using [uv](https://docs.astral.sh/uv/) to install this project directly for development.

```bash
git clone https://www.github.com/sdss/explorer.git ./sdss-explorer
cd sdss-explorer
uv sync
```

Otherwise, install like any other package:

```bash
git clone https://www.github.com/sdss/explorer.git ./sdss-explorer
cd sdss-explorer
python -m .venv venv # ensure you're using python 3.10
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```


### Data files
Explorer uses stacked, custom HDF5 renders of the [astra](https://github.com/sdss/astra) summary files for each data release. You can download the HDF5's from [here](https://data.sdss5.org/sas/sdsswork/users/u6054929/). These are proprietary SDSS data files, and should not be shared outside the collaboration.

It additionally uses a custom parquet render of the mappings used in [semaphore](https://github.com/sdss/semaphore), available in the same directory.

## Starting the server
To run, the environment variables must be exported to the shell environment. The base ones are:

 - `EXPLORER_DATAPATH` :: path to data files (proprietary SDSS data, found on the SAS). 
    - In the deployment context a folder is mounted onto the VM.
    - Files are expected to be placed as: `./[release]/[explorer|columns]All[datatype]-[vastra].[hdf5|parquet]`
 - `VASTRA` :: specific [astra](https://github.com/sdss/astra) reduction versions to read.
 - `VAEX_HOME` :: path to store cache and log files during runtime. Defaults on startup to `$HOME/.vaex`.
 - `VALIS_API_URL` :: url for [valis](https://www.github.com/sdss/valis). This is required for login authentication (to be implemented).

Additionally, using the download server requires:
 - `EXPLORER_SCRATCH` :: path to a scratch space
 - `API_URL` :: API url for the download server. Defaults to localhost (so you might not need to set this)
 - `EXPLORER_NPROCESSES` :: max concurrent processes for custom summary file renders.

 You also must additionally set for the Docker:
 - `EXPLORER_NWORKERS` :: how many gunicorn/uvicorn workers to use

### Cache setup
The Explorer can utilize a hybrid memory and disk cache . To set these up, use the following environment variables on runtime:
 - `VAEX_CACHE="memory,disk"`
 - `VAEX_CACHE_DISK_SIZE_LIMIT="10GB"` -- this can be higher/lower
 - `VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB` -- this can also be higher/lower

These are automatically set when using the bundled shell scripts and docker.


## Deployment

### Individually

To run the dashboard, use:
```bash
solara run sdss_explorer.dashboard
```

Then, run the `FastAPI` backend with:
```bash
uvicorn --reload sdss_explorer.server:app --port=8050
```

This will start _purely_ the app in development refresh mode on two uvicorn instances. To run in production mode, add `--production` to the `solara` command, and remove the `--reload` flag from the `uvicorn` call.

### Docker
This repo comes included with a basic production docker image.

To build, run:
```bash
docker build -t explorer -f Dockerfile .
```

To start a container, run:
```bash
docker run -p 8050:8050 -v $EXPLORER_SCRATCH:/root/scratch valis-dev -v $EXPLORER_DATAPATH:/root/data -e EXPLORER_DATAPATH=/root/data -e EXPLORER_SCRATCH=/root/scratch
```
Additionally, add `-e EXPLORER_MOUNT_DASHBOARD` to mount the dashboard to the same docker.

### Bundled shell scripts
This repo comes bundled with shell scripts to run the application via `solara`. They don't particularly do anything different to just running it manually. To ensure they work, make the scripts executable:
```bash
chmod +x run.sh run_production.sh
```

To run using the provided shell scripts, use one of:
```bash
./run.sh # runs development mode
```
or
```bash
./run_production.sh # runs in production mode; no auto-refresh
```



## Valis

This application is currently embedded in the SDSS [valis](https://www.github.com/sdss/valis) API for deployment. You can test and develop the app within this deployment context through a `poetry install`:
```
git clone https://github.com/sdss/valis.git
cd valis
poetry install -E solara
```

Load the relevant created virtual environment (generally in poetry cache unless stated otherwise) and deploy as:
```
uvicorn valis.wsgi:app --reload
```

The local web server is exposed at `http://localhost:8000`, with the solara app at `http://localhost:8000/valis/solara/dashboard`.


---
# License
This project is Copyright (c) 2024, Riley Thai. All rights reserved.

# Contributing
We love contributions! `explorer` is open source, built on open source, and we`d love to have you hang out in our community.

Imposter syndrome disclaimer: We want your help. No, really.

There may be a little voice inside your head that is telling you that you're not ready to be an open source contributor; that your skills aren't nearly good enough to contribute. What could you possibly offer a project like this one?

We assure you - the little voice in your head is wrong. If you can write code at all, you can contribute code to open source. Contributing to open source projects is a fantastic way to advance one's coding skills. Writing perfect code isn't the measure of a good developer (that would disqualify all of us!); it's trying to create something, making mistakes, and learning from those mistakes. That's how we all improve, and we are happy to help others learn.

Being an open source contributor doesn't just mean writing code, either. You can help out by writing documentation, tests, or even giving feedback about the project (and yes - that includes giving feedback about the contribution process). Some of these contributions may be the most valuable to the project as a whole, because you're coming to the project with fresh eyes, so you can see the errors and assumptions that seasoned contributors have glossed over.

Note: This disclaimer was originally written by Adrienne Lowe for a PyCon talk, and was adapted by `explorer` based on its use in the README file for the MetPy project.
