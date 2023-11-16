import pandas as pd
import vaex as vx
import plotly.express as px

df_sample = vx.open(
    "/home/riley/uni/rproj/data/allApogeeNetStar-0.4.0.parquet")

x = df_sample["TEFF"].values
y = df_sample["LOGG"].values
c = df_sample["FE_H"].values

px.scatter(x=x, y=y, color=c)
