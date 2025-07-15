A high-speed, performant data exploration webapp for astronomy, built for SDSS-V.

![[main app]](assets/main.png)

## Highlights

* _Blazing fast cross-filtering, powered by `vaex`._
* _Dynamic, interactive plotting, powered by `Bokeh`._
* _Modular support for various data releases_
* _Download custom summary outputs direct from the app_
* _Share your dashboard layout with others via simple JSON_
* _Modular support for various data releases_

## About

The Explorer is SDSS-V's interface for accessing and exploring Milky Way Mapper stellar parameters provided by Astra for SDSS-V targets. The Explorer is designed to provide a high-speed interface for aggregated statistics and visualizations of filtered _Subsets_ of the SDSS-V database.

Explorer is developed by SDSS-V, using `solara`, `fastapi`,`vaex`, and `bokeh`. Explorer was developed and designed by Riley Thai, and is maintained by the SDSS-V Data Visualization Team.

!!! note
    The examples and screenshots in these docs may reference the `best` Astra summary catalog file.  This file has now been named `mwmLite`.  In the live dashboard you will see reference to the `mwmlite` dataset.  This is the same as `best` in this documentation.

Get started with our examples:

* [Example: creating a HR diagram](examples/hr.md)
* [Example: selecting sources from Gaia](examples/crossmatch.md)
* [Example: selecting a carton](examples/yso.md)
* [Example: comparing flags and datasets](examples/flags.md)
* [Example: getting your data out](examples/download.md)
* [User guide](user/plotting.md)

And see some more documentation at:

* [Developer guide](developer/)
* [Reference (API)](reference/sdss_explorer)


---
Explorer and these documents were written, designed, and primarily developed by Riley Thai.
