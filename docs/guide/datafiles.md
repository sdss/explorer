# Data files
The Explorer uses custom HDF5, parquet, and JSON files for its application. Data files for the SDSS Explorer are stored at [this directory](https://data.sdss5.org/sas/sdsswork/users/u6054929) on CHPC Utah.

## Data file types

### explorerAllVisit and explorerAllStar (HDF5) 

Each of the `explorerAllVisit.hdf5` and `explorerAllStar.hdf5` files are *stacked* versions of the `astraAllStar` and `astraAllVisit` FITS summary files produced by [`sdss/astra`](https://github.com/sdss/astra) after each run.

All data within these are stored as [Apache Arrow datatypes](https://arrow.apache.org/docs/python/api/datatypes.html) to ensure maximum access and filtering speed ***except for 2D columns***, such as `sdss5_target_flags` or similar nested lists. Nested lists are instead stored as [numpy arrays](https://numpy.org/) for efficient filtering and data access.


#### Accessing each dataset

To differentiate each dataset, one can use the `pipeline` column.
```python
import vaex as vx
df = vx.open("explorerAllStar.hdf5")# a Vaex DataFrame

dff = df[df['pipeline == "aspcap"']] # dff has the exact same data as astraAllStarASPCAP.fits.gz
```

In Explorer, this filtering step is done first, and then an extracted DataFrame object is stored with each **Subset**, which improves performance by restricting new filters to the rows of the selected dataset. This process is managed by `task` in TODO SubsetUI.

```python
# continuing from above; this is what the app does under the hood

Subset.df = dff.extract() # now when doing new filters, they are only applied to the rows in dff, and not df
```
### Columns JSON

The `columnsAllStar` and `columnsAllVisit` assist with guardrailing users and downloading by allowing the app to efficiently selecting columns that have no NaN values. 

These `columns` JSON files are loaded as `dict[str]` to **TODO** `StateData.columns`, which is then accessed to fill `Subset.columns` on each `dataset`/`pipeline` update. 

Computing which columns are all nan per dataset switch within the app live was ineffecient. Precompiling them is a trivial operation and takes minimal memory/CPU to load.


### Mappings parquet
`mappings.parquet` is a compiled datafile of all the `sdss` targeting cartons and programs, which is used by the **TODO** `Targeting Filters Panel`. 

# Generating new data files

Generation of new datafiles requires the use of a computer with lots of memory due to the size of the merge operation, which requires that the entire dataset fits into memory (i.e. a cluster).

Generation can be done with the `sdss_explorer.filegenerator` module and takes three steps.

1. Source all current astra summary data files (*link to function that does this here*).
    * For `spall`, we use the BOSS pipeline summary files 
        * `spAll-lite` for visit 
        * `spAll-lite_multimjd` for star, since many BOSS-only sources (like quasars) have no real "star" coadd equivalent.
2. Convert all astra summary files to arrow (parquet), then HDF5.
    * `vaex` can't load `fits` files since `vaex.astro` hasn't been updated in some time, so we use Bristol's `STILTS` (part of TOPCAT) to convert them to `parquet`.
        * This requires the `topcat-extra.jar` file.
        * Note that this process drops the `tags` and `carton_0` columns.
    * This also automagically ensures that ALL datatypes are Apache Arrow
    * When we reconvert back to HDF5, we additionally ensure that *any* `pa.ChunkedArray` (list of list) datatypes are converted back into `numpy` datatypes to ensure compatibility.
3. Merge all files together and output `columns*.json`
    * Columns files are used for guardrailing, see [here](guardrailing.md).

Within the `misc` folder, you will find additional slurm commands and scripts to run the generators via `sbatch`.
