Subsets are different _mutations_ of the dataset that you can create, filter, visualize and download. You can create as many _Subsets_ as you like, and perform a variety of filtering options

#### Filtering

Filtering uses a combination of:

* _Expressions_: a custom filter expression to apply
* _Dataset_: the stellar parameters pipeline used.
* _Targeting Filters_: specific groups of `sdss5` targets from different programs, mappers, or targeting cartons
* _Quick Flags_: some simple flags for users. We default to having `purely non-flagged` data shown to users.
* _Crossmatch_: specific identifiers to filter down to.

#### Dataset

Within SDSS-V, multiple stellar parameters pipelines are used. For a valid analysis, one must choose a specific pipeline output to use for analysis.

By default, we use the `astraMWMLite` parameters for simplicity, as described [**here (sdss.org/dr19)**](https://www.sdss.org/dr19/mwm/astra/pipelines-in-astra/bestparams/). Remember that this is largely a "stepping stone", and no guarantee is made about scale consistency in stellar parameters from different pipelines.

#### Downloading

You can download your subset by clicking on the button in the bottom left of the Subset card.

Note that plot selections are not included in your download outputs.

For more information, see [Downloading data](download.md).
