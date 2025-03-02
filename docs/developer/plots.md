Let's talk plots, shall we?


Plots are arguably the _most_ complex part of this codebase, namely because the majority of interactive plotting libraries are not built for integrations with Solara. They're built for `Panel` or `Dash` or similar.

As such, we make a number of extensive modifications and create a number of methods to allow plots to be used interactively with high efficiency.


Within [`sdss_explorer.dashboard.components.views`](../../reference/sdss_explorer/dashboard/components/views), we use the following:

* [`plots`](../../reference/sdss_explorer/dashboard/components/views/plots) : front-end components of plots themselves.
* [`plot_actions`](../../reference/sdss_explorer/dashboard/components/views/plot_actions) : for defining specific ways plots are updated, like `reset_range` or `change_formatter`.
* [`plot_utils`](../../reference/sdss_explorer/dashboard/components/views/plot_utils) : utility functions, used to both generate plot objects and do interim calculations
* [`plot_effects`](../../reference/sdss_explorer/dashboard/components/views/plot_effects) : the hooks that allow plots to update on `PlotState` changes.
* [`plot_themes`](../../reference/sdss_explorer/dashboard/components/views/plot_themes) : the theming and color specs for plots
* [`grid`](../../reference/sdss_explorer/dashboard/components/views/plot_themes) : the overarching component that controls the grid layout.

The relevant settings for plots are stored in the [`PlotState`](../../reference/sdss_explorer/dashboard/dataclass/plotstate#PlotState).

We'll go over each submodule in brief. 

### Plots

These are the front end components, which connect actual plot objects to effects, to widget conversion via [`FigureBokeh`](../../reference/sdss_explorer/dashboard/components/views/figurebokeh) and the dataframe of the subset from the [`SubsetState`](../../reference/sdss_explorer/dashboard/dataclass/subsets).

The general steps are:

1. we instantiate hooks to the Subset and the filter mechanism
2. we get our filtered dataframe **every render** -- this ensures it is always up to date no matter what, and since `vaex` performs zero-copy access this is virtually costless.
3. we memoize a `ColumnDataSource` and `Plot` object, to be excluded from rerenders
   * this approach allows us to edit them via their pointer directly between different renders, instead of rebuilding the object each time.
   * this is the _only_ way to have certain updates be parsed properly in certain cases.
4. we add the effects

### Plot actions

Plot actions hold general methods to avoid boilerplate code. Things like resetting ranges, changing formatters, and updating axes are held here in nice methods.

### Plot utils

This is every utility and generation function, used to create specific Bokeh objects and perform some intermediate calculations

### Plot effects

These are the specific callbacks which trigger on plot settings changes.


## Some notes

* Bokeh's categorical scales are not hot-swappable -- you have to jump through hoops to do them properly. As such, we do all categorical mapping ourselves, not client side. This is pretty efficient to map, and it is the only way in some cases to access category-like data.
* Any effect that is spammable is be debounced to avoid losing the WebSocket connection.
