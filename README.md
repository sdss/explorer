# PHS3350
*Nov 16, 2023 -- Feb 17, 2024*

## Explorer

The SDSS Explorer, vaex dashboard, or visboard (or whatever we should call it we have not decided a name) is a custom data visualization application developed for SDSS-V's DR19, built using `solara`, `plotly` and `vaex`.

### Installation

Ensure that a new virtual environment is created prior to installation
```
python3.10 -m venv venv
```
or for Anaconda distributions, run:
```
conda create -n sdss-explorer python=3.10 solara=1.27.0
```

To install in this `venv`, run:

```
git clone https://www.github.com/rileythai/phs3350.git ./sdss-explorer
cd sdss-explorer
pip install . -e
```

### Run Server

To run, the environment variables must be exported to the shell environment. These are:

 - `EXPLORER_PATH` :: path to data files (prioprietary SDSS data)

After this, one can run using any of the commands below.

To make the shell scripts executable, run:
```
chmod +x run.sh run_production.sh
```
To run, use any of:
```
./run.sh

./run_production.sh

solara run explorer.pages
```

## SDSS-V loaders (specutils)
See [here](https://www.github.com/astropy/specutils/pull/1107).
