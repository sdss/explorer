# Explorer

The SDSS Explorer, vaex dashboard, or visboard (or whatever we should call it we have not decided a name) is a custom data visualization application developed for SDSS-V's DR19, built using `solara`, `plotly` and `vaex`.

## Installation

Ensure that a new virtual environment is created prior to installation
```
python3.10 -m venv venv
```
or for Anaconda distributions, run:
```
conda create -n sdss-explorer python=3.10 solara=1.27.0
```

To install in this `venv`, run one of the following:

To just install it, run:
```
pip install git+https://www.github.com/sdss/explorer.git@main
```
or, to have a local copy for development on your machine, clone and install as an editable package:
```
git clone https://www.github.com/sdss/explorer ./sdss-explorer
cd sdss-explorer
pip install -e .
```

## Starting

To run, the environment variables must be exported to the shell environment. These are:

 - `EXPLORER_DATAPATH` :: path to data files (prioprietary SDSS data, found on the SAS).
 - `VALIS_API_URL` :: url for [valis](https://www.github.com/sdss/valis). This is required for login functionality.

there will likely be more in future.

After this, one can run by using:
```
solara run explorer.pages --theme-variant dark
```

### Bundled shell scripts
This repo comes bundled with shell scripts to run the application via `solara`. They don't particularly do anything different to just running it manually. To ensure they work, make the scripts executable:
```
chmod +x run.sh run_production.sh
```

To run using the provided shell scripts, use:
```
./run.sh
```

```
./run_production.sh
```


---
# License
This project is Copyright (c) 2024, Riley Thai. All rights reserved.

# Contributing
We love contributions! `explorer` is open source, built on open source, and we'd love to have you hang out in our community.

Imposter syndrome disclaimer: We want your help. No, really.

There may be a little voice inside your head that is telling you that you're not ready to be an open source contributor; that your skills aren't nearly good enough to contribute. What could you possibly offer a project like this one?

We assure you - the little voice in your head is wrong. If you can write code at all, you can contribute code to open source. Contributing to open source projects is a fantastic way to advance one's coding skills. Writing perfect code isn't the measure of a good developer (that would disqualify all of us!); it's trying to create something, making mistakes, and learning from those mistakes. That's how we all improve, and we are happy to help others learn.

Being an open source contributor doesn't just mean writing code, either. You can help out by writing documentation, tests, or even giving feedback about the project (and yes - that includes giving feedback about the contribution process). Some of these contributions may be the most valuable to the project as a whole, because you're coming to the project with fresh eyes, so you can see the errors and assumptions that seasoned contributors have glossed over.

Note: This disclaimer was originally written by Adrienne Lowe for a PyCon talk, and was adapted by sdss_solara based on its use in the README file for the MetPy project.
