**known bugs:**
  - there are weird artifacts in the count algorithm.
  - setting any other filter then typing an expression causes the expression code to explode on an AssertionError, vaex fails (for some reason).
  - vaex cannot count catagorical data (i.e. telescope). 
    - I have a manual implementation of it for now.
  - upon changing to catagorical data, the histogram does not immediately realize and stays in numeric mode. a parameter must be changed first (binsize, even though it doesnt affect anything)
    - this appears to be a plotly bug, or maybe a solara bug

**needed features:**
  - needs to exit plot without crashing app when expression is entered that reduces the minmax to a stride less than 1.
  - range sliders? specifically for the imshow plot to allow for higher resolution

**my fixes to likely common bugs**
  - must wrap entered expressions in brackets for expression editors, otherwise AND operation fails.
