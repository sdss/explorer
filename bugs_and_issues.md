**known bugs:**
  - solara's cross filter kills itself when pivot table and expression are set simultaneously.

  - there are weird artifacts in the count algorithm.
  - vaex cannot count catagorical data (i.e. telescope). 
    - I have a manual implementation of it for now.

**needed features:**
  - needs to exit plot without crashing app when expression is entered that reduces the minmax to a stride less than 1.
  - range sliders? specifically for the imshow plot to allow for higher resolution


**my bugs:**
  - upon changing to catagorical data, the histogram does not immediately realize and stays in numeric mode. a parameter must be changed first (binsize, even though it doesnt affect anything)

