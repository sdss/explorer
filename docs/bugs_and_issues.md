**known bugs:**
  - there are weird artifacts in the count algorithm.
  - vaex cannot count catagorical data (i.e. telescope). 
    - I have a manual implementation of it for now.
    - i think there is ds.count_unique()
  - upon changing to catagorical data, the histogram does not immediately realize and stays in numeric mode. a parameter must be changed first (binsize, even though it doesnt affect anything)
    - this appears to be a plotly bug, or maybe a solara bug
  - on settting a filter, the layout bugs out and crashes the imshow plot
- At certain binsizes, there are weird artifacts in the counting algorithm.
- Scatter selections may crash other plot views (`stride less than one` error in `vaex/cpu.py`)
- Upon setting a filter, the `aggregated` view crashes (`imshow template` error)
  - this may be an issue with my dev `venv`, so it might work fine for you
- the resize indicator is not properly aligned to the edge of the bins
- `Plotly.js` has a bug where plot widgets do not dynamically resize to the height of their container.
  - it also happens on the width of the scatter plot if you set to 'Flip' any of the axes
- the application will crash if you choose to plot silly columns
- upon setting `histogram` to a catagorical data column, it does not redraw properly.
- NOTE: the dynamic redraw for `scatter` is disorienting and really weird
  - it can be disabled in the settings of the view panel.
  - I've implemented it mainly as a proof of concept for dynamic redrawing in this tech stack, similar to [holoviz/datashader](https://github.com/holoviz/datashader)
- scatter selections don't deselect
- **BREAKING:** the skyplot is really really laggy for some reason now, i think the amount of hooks is breaking it
**needed features:**
  - range sliders? specifically for the imshow plot to allow for higher resolution
  - change from nbins to binsize
  - underlying scatter visualization

**my fixes to likely common bugs**
  - must wrap entered expressions in brackets for cross filters, otherwise the AND operation fails.
  - if encountering an AssertionError on b.ds == a.ds error during crossfiltering with vaex, remember that the filter must be applied to the ORIGINAL dataframe pointer, and not the filtered copy.
    - this ensures the reference datasets are the same (b.ds == a.ds)
