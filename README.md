# Explorer

The SDSS Parameter Explorer is a custom data visualization application developed for SDSS-V's DR19, built using `solara`, `plotly` and `vaex`. It is designed to specifically interface with custom SDSS summary parquet files, providing filtered access, statistics, and visualization to the Astra parameters of `sdss5db`.

## Installation

Ensure that a new virtual environment is created prior to installation
```
python3.10 -m venv venv
pip install solara=1.30.0 vaex pandas
```
or for Anaconda distributions, run:
```
conda create -c conda-forge -n sdss-explorer python=3.10 solara=1.30.0 vaex
```

To install in this `venv`, run one of the following:

To just install it tracking `main`, run:
```
pip install git+https://www.github.com/sdss/explorer.git@main
```
or, to have a local copy for development on your machine, clone and install as an editable package via `pip`:
```
git clone https://www.github.com/sdss/explorer.git ./sdss-explorer
cd sdss-explorer
pip install -e . 
```

### Data files
Currently, the dashboard uses custom parquet versions of the Astra allStar summary files from each pipeline. You can download the parquet files from [here](https://data.sdss5.org/sas/sdsswork/users/u6054929/). These are proprietary SDSS data files, and should not be shared outside the collaboration.

The app uses two files:
- `ipl3-partial.parquet` :: a parquet of 3 allStar parameter files (APOGEENet, ASPCAP, The Cannon) -- to be expanded upon with more
- `mappings.parquet` :: a converted version of the `bitmappings.csv` used in [sdss/semaphore](https://github.com/sdss/semaphore), for creating filters for cartons and mappers

## Starting the server
To run, the environment variables must be exported to the shell environment. These are:

 - `EXPLORER_DATAPATH` :: path to data files (proprietary SDSS data, found on the SAS). In the deployment context a folder is mounted onto the VM.
 - `VALIS_API_URL` :: url for [valis](https://www.github.com/sdss/valis). This is required for login authentication (to be implemented).
 - `VAEX_HOME` :: path to store `vaex` cache and lock files during runtime. Defaults on startup to `$HOME/.vaex`.

### Cache setup
The Explorer utilizes a hybrid memory cache of 1GB per worker and disk cache of total 10GB. To set these up, use the following environment variables on runtime:
 - `VAEX_CACHE="memory,disk"`
 - `VAEX_CACHE_DISK_SIZE_LIMIT="10GB"`
 - `VAEX_CACHE_MEMORY_SIZE_LIMIT="1GB`

 These are automatically set when using the bundled shell scripts.



## Deployment

### Solara Server deployment (starlette)

One can run using Solara's starlette deployment by using:
```
solara run explorer.pages --theme-variant dark
```

This will start _purely_ the app in development refresh mode on a uvicorn instance. To run in production mode, add `--production` to the above command.

### Bundled shell scripts
This repo comes bundled with shell scripts to run the application via `solara`. They don't particularly do anything different to just running it manually. To ensure they work, make the scripts executable:
```
chmod +x run.sh run_production.sh
```

To run using the provided shell scripts, use one of:
```
./run.sh
```
or
```
./run_production.sh
```

### Valis

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
