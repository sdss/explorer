currently reads a set of files local to the server dir, which is likely _not_ going to be the setup on production servers.

so, to read over SSH tunnel or something, this will require 2 things:

1. server side, we store 
     - having a pipeline update this is OPTIONAL at this state
2. using `sdss_access`  a db connection
3. read over the db connection with `vaex`

alternatively, it just copies the files to the server and it works fine.

ALSO OTHER NOTE:

for AppBar at top of screen, do the following:
1. theme button
2. accessibility settings (opens dialog)
3. dataset menu (need to shrink its length)
   - still need to discuss dataset storage solution as it will determine UI side integration(s)
4. auth button (for SDSS working login dialog)

on dataset storage methods:
1. each pipeline outputs a DR19 parquet (for both public DR19/20 and working)
   - to multi-load these, visboard merges them via vaex every time
     - issue: dataframe object will change -> need to ensure filters are preserved in the CrossFilterStore (solara)
       - if the df is updated, all expression objects need to be regenerated in the CrossFilterStorage, then passsed down accordingly (can be integrated as a task)
  - likely the easiest to support for working & public splits.
2. 1 gigantic DR19 summary file with outputs from EVERYTHING (2 files, 1 public, 1 working)
  - very bad for working groups, multiple continuous writes to files
  - fine for public: although if the file is on a CDN, it gets iffy to store this massive thing
