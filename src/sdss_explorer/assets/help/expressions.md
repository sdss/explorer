mdi-math-integral-box
### Expressions
_Expressions_ refer to columnar data-based filters you can apply onto the subset. The exact syntax uses generic, Python-like modifiers, similarly to the `pandas` DataFrame protocol. 

For example, you can enter:

    teff < 9e3 & logg > 2

to apply a filter for $T_{\mathrm{eff}} < 9000$ and $\log g > 2$ across the SDSS dataset.

Similarly, you can enter more advanced expressions like:

    (teff < 9e3 | teff > 12e3) & fe_h <= -2.1 & result_flags != 1

