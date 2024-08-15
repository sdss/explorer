mdi-calculator
### Virtual Calculations
Virtual calculations are out-of-memory calculations and manipulations you can perform on the columnar data directly from the _Explorer_ webapp interface.

All calculations are processed server-side, without any local downloads required.

The functionality mirrors how one could download and use the dataset locally, calculating important data from the data within the dataset.


#### Example
Let's say we want to use the Gaia parallaxes (`plx`) and magnitudes (`g_mag`) to _roughly_ calculate surface gravities.

We can enter this as a new column by clicking on the _Virtual Calculations_ menu and adding a column.

The formula is simply:

$$\log g_{\mathrm{plx}} = \log g_{\odot} + \log \left( \frac{M_{\star }}{M_{\odot}} \right) +4 \log \left( \frac{T_{\mathrm{eff}}}{T_{\mathrm{eff},\odot}} \right) +0.4 (M_{\mathrm{bol}} - M_{\mathrm{bol},\odot})$$


where $\log g_{\odot} = 4.44$ and $M_{bol,\odot} = 4.75}$ and $T_{\rm eff} = 5770$.

The bolometric magnitude, excluding extinction and bolometric correction, is given by:

$$M_{bol} \approx G + 5 \log(\omega \times 10^{-3}) + 5$$

where $G$ is the Gaia magnitude, and we convert parallax $\omega$ from milliarcseconds to arcseconds.

This can be written in the virtual column syntax for an ASPCAP subset, with the columns `mass`, `teff`, and `g_mag` as:
  
    4.44 + log10((mass)) + 4*log10((teff/5770)) + 0.4*(g_mag + 5*log10(plx) + 5 - 4.75)

