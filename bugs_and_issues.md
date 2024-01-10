**known bugs:**
  - there are weird artifacts in the count algorithm.
  - vaex cannot count catagorical data (i.e. telescope). 
    - I have a manual implementation of it for now.
    - i think there is ds.count_unique()
  - upon changing to catagorical data, the histogram does not immediately realize and stays in numeric mode. a parameter must be changed first (binsize, even though it doesnt affect anything)
    - this appears to be a plotly bug, or maybe a solara bug
  - on settting a filter, the layout bugs out and crashes the imshow plot

**needed features:**
  - range sliders? specifically for the imshow plot to allow for higher resolution

**my fixes to likely common bugs**
  - must wrap entered expressions in brackets for cross filters, otherwise the AND operation fails.
  - if encountering an AssertionError on b.ds == a.ds error during crossfiltering with vaex, remember that the filter must be applied to the ORIGINAL dataframe pointer, and not the filtered copy.
    - this ensures the reference datasets are the same (b.ds == a.ds)
