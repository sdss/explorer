# Data files
The Explorer uses custom HDF5, parquet, and JSON files for its application. Data files for the SDSS Explorer are stored at [this directory](https://data.sdss5.org/sas/sdsswork/users/u6054929) on CHPC Utah.

## Data file types

### explorerAllVisit and explorerAllStar (HDF5) 

Each of the `explorerAllVisit.hdf5` and `explorerAllStar.hdf5` files are *stacked* versions of the `astraAllStar` and `astraAllVisit` FITS summary files produced by [`sdss/astra`](https://github.com/sdss/astra) after each run.

All data within these are stored as [Apache Arrow datatypes](https://arrow.apache.org/docs/python/api/datatypes.html) to ensure maximum access and filtering speed ***except for 2D columns***, such as `sdss5_target_flags` or similar nested lists. Nested lists are instead stored as [numpy arrays](https://numpy.org/) for efficient filtering and data access (because `vaex` doesn't support 2D Arrow data yet).


#### Accessing each dataset

To differentiate each dataset, one can use the `pipeline` column.
```python
import vaex as vx
df = vx.open("explorerAllStar.hdf5")# a Vaex DataFrame

dff = df[df['pipeline == "aspcap"']] # dff has the exact same data as astraAllStarASPCAP.fits.gz
```

In Explorer, this filtering step is done first, and then an extracted DataFrame object is stored with each **Subset**, which improves performance by restricting new filters to the rows of the selected dataset. This process is managed by a task `task` in [`DatasetSelect`](../../reference/sdss_explorer/dashboard/components/sidebar/subset_filters/#sdss_explorer.dashboard.components.sidebar.subset_filters.DatasetSelect).

```python
# continuing from above; this is what the app does under the hood

Subset.df = dff.extract() # now when doing new filters, they are only applied to the rows in dff, and not df
```
### Columns JSON

The `columnsAllStar` and `columnsAllVisit` assist with guardrailing users and downloading by allowing the app to efficiently selecting columns that have no NaN values. 

These `columns` JSON files are loaded as `dict[str]` to [`State.columns`](../../reference/sdss_explorer/dashboard/dataclass/state#StateData), which is then accessed to fill [`Subset.columns`](../../reference/sdss_explorer/dashboard/dataclass/subset#Subset) on each `dataset`/`pipeline` update. 

Computing which columns are all `nan` per `dataset` switch within the app live was inefficient. Precompiling them is a trivial operation and takes minimal memory/CPU to load.


### Mappings parquet
`mappings.parquet` is a compiled datafile of all the `sdss` targeting cartons and programs, which is used by the [`filter_carton_mapper` function](../../reference/sdss_explorer/util/filters#filter_carton_mapper) for selecting cartons and mapper programs.

!!! warning
    `mappings.parquet` is not generated via the datafile generation described below. It must be generated manually (trival via `pandas`) from any updated `bitmappings.csv` file in [`sdss/semaphore`](https://github.com/sdss/semaphore).


### Column glossary (dminfo)
The column glossary uses a custom `JSON` file built from the [`sdss/datamodel`](https://github.com/sdss/datamodel) package data specification files. It holds descriptors for each of the columns across all summary files.

The filename is formatted as `[release (lowercase)]_dminfo.json`, and stored in the root directory of the datapath.

# Generating new data files

Generation of new datafiles requires the use of a computer with lots of memory due to the size of the merge operation, which requires that the entire dataset fits into memory.

Generation can be done with the files in [`sdss/explorer-filegen`](https://github.com/sdss/explorer-filegen) repository and takes three steps.

1. Source all current `astra` summary data files + relevant `spAll` files and place into a subdirectory corresponding to the `astra` version.
    * Place these in some working directory with enough space to store upwards of 100GB of total data.
    * For `spall`, we use the BOSS pipeline summary files 
        * `spAll-lite` for visit .
        * `spAll-lite_multimjd` for star, since many BOSS-only sources (like quasars) have no real "star" coadd equivalent.
2. Convert all astra summary files to arrow (parquet), then HDF5.
    * `vaex` can't load `fits` files since `vaex.astro` hasn't been updated in some time, so we use Bristol's `STILTS` (part of TOPCAT) to convert them to `parquet`.
        * This requires the `topcat-extra.jar` file.
        * Note that this process drops the `tags` and `carton_0` columns.
    * This also automagically ensures that ALL datatypes are encoded as Apache Arrow ones.
    * When we reconvert back to HDF5, we additionally ensure that *any* nested `pa.ChunkedArray` (list of list) datatypes are converted back into `numpy` datatypes to ensure compatibility.
    * **NOTE:** you must convert `spAll-lite` files used in the stacks __manually__ using `spall_convert.py`.
3. Merge all files together and output `columns*.json`
    * Columns files are used for guardrailing and efficiency, see [here](guardrailing.md).
4. Generate custom datamodels for Column Glossary
    * This uses the script in `sdss/explorer/scripts`, and uses the [`datamodel`](https://github.com/sdss/datamodel) interface to compile a JSON directly.

Within the repository, you will find additional slurm commands and scripts to run the generators (only steps 2 and 3) via `sbatch`.
