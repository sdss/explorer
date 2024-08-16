mdi-calculator
### Virtual Calculations
Virtual calculations are out-of-memory calculations and manipulations you can perform on the columnar data directly from the _Explorer_ webapp interface.

The functionality mirrors how one could download and use the dataset locally, calculating new quantities from the columns within the dataset. All calculations are processed server-side, however, without any local downloads required.

---

### Example: parallax surface gravity
We can _roughly_ calculate surface gravity from the Gaia parallaxes (`plx`) and magnitude (`g_mag`). The formula for a star of $1\mathrm{M_\odot}$ is simply:

$$\log g_{\mathrm{plx}} = \log g_{\odot} + 4 \log \left( \frac{T_{\mathrm{eff}}}{T_{\mathrm{eff},\odot}} \right) +0.4 (G + 5 \log(\omega \times 10^{-3}) + 5 - M_{\mathrm{bol},\odot})$$

Note that $G$ is the Gaia G magnitude, we convert parallax $\omega$ from milliarcseconds to arcseconds. In this example, we do not add extinction effects, but the relevant column does exist in the dataset.

We can enter this as a new column by clicking on the _Virtual Calculations_ menu and adding a column. This can be written in the virtual column syntax for an ASPCAP subset, with the columns `mass`, `teff`, and `g_mag` as:

    4.44 + 4*log10(teff/5770) + 0.4*(5*log10(plx*1e-3) + 0.25 + g_mag)

where $\log g_{\odot} = 4.44$ and $M_{bol,\odot} = 4.75}$ and $T_{\rm eff} = 5770$.
