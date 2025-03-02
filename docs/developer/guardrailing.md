# Guardrailing

To ensure users do not do unanticipated actions that they may not want to do, we have a series of basic guardrails.

## Allowed columns JSON

In each release's data directory, there are files `columnsAllStar-VASTRA.json` and `columnsAllVisit-VASTRA.json`. These are used as global column lookups within the [`State` dataclass](../reference/sdss_explorer/dashboard/dataclass/state#StateData) for use with suggesting columns that will have data in plot settings menus.

## Loaded default flags

In SDSS, we have a couple of things that go wrong (bad observations, bad data reductions, weird data stuff), so we denote these with flags.

To ensure users don't do something very silly, we (by default) apply a blanket flag which removes most of our poor data. This is set by default as `purely non-flagged`. This flag is enabled by default for each new Subset.
