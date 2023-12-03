import vaex
import solara
from solara.components.dataframe import *

# df = vaex.datasets.titanic()
# df = vaex.open('/data/stsci/single.hdf5')
# df = vaex.open("/Users/maartenbreddels/data/yellow_taxi_2009_2015_f32_from_parquet_filtered.hdf5")
df = vaex.open("/home/riley/Downloads/stsci-mast.hdf5")
# first 100 million rows
df = df  # @[:1_000_000]

vaex.cache.on("memory")


@solara.component
def STScI(df):
    with solara.Columns([50, 50]):
        SummaryCard(df)
        # DropdownCard(df, "vendor_id")
        DropdownCard(df, "filters")
        # DropdownCard(df)
    with solara.Columns([25, 50, 25]):
        HeatmapCard(
            df,
            "s_ra",
            "s_dec",
        )

        # solara.PivotTableCard(df, x=['passenger_count'], y=['payment_type'])
        solara.PivotTableCard(df, x=["dataproduct_type"], y=["obs_collection"])
        HistogramCard(df)


page = STScI(df)
page
