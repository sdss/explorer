This app has state for different components placed into

You may notice that all names are postpended with `Data`. Here, we use classes to create them, but create seperate classes with methods. This makes API documentation cleaner and the namespaces more Pydantic-like.


# State

State is used to hold certain app-wide state variables that control the app itself.

## API

::: sdss_explorer.dashboard.dataclass.state.StateData

# SubsetState

SubsetState specifically holds Subset dataclasses, which are used to generate the components in the sidebar. These also hold specific `vx.DataFrame` instances which correspond to plots.


## Subset

::: sdss_explorer.dashboard.dataclass.subsets.Subset

## API

::: sdss_explorer.dashboard.dataclass.subsets.SubsetData

# VCData

Used to hold the current virtual columns. Handles add and remove operations in the backend.

## API

::: sdss_explorer.dashboard.dataclass.vcdata.VCList


# GridState

Used to control the grid layout

## API

::: sdss_explorer.dashboard.dataclass.gridstate.GridData

# PlotState

`PlotState` is a specific class of plot settings that is instantiated and used in individual plot inistances. See more in [Plots](plots.md).
