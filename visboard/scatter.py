"""
Interactive scatter plot testing

"""
from typing import Optional, cast

import vaex as vx
import solara as sl
import solara.express as solara_px
import plotly.express as px

import numpy as np

# dataframe loader
df = vx.open("/home/riley/uni/rproj/data/allApogeeNetStar-0.4.0.parquet")
df = df[:int(0.3 * len(df))]
# df = vx.example()

keys = df.get_column_names()


class State:
    color = sl.reactive(cast(Optional[str], None))
    x = sl.reactive(cast(Optional[str], None))
    y = sl.reactive(cast(Optional[str], None))
    logx = sl.reactive(False)
    logy = sl.reactive(False)
    df = df

    @staticmethod
    def load_sample():
        State.x.value = str("TEFF")
        State.y.value = str("LOGG")
        State.color.value = str("FE_H")
        State.logx.value = True
        State.df = df


@sl.component
def Page():
    df = State.df

    with sl.Sidebar():
        with sl.Card("Controls", margin=0, elevation=0):
            with sl.Column():
                if df is not None:
                    sl.Checkbox(label="Log x", value=State.logx)
                    sl.Checkbox(label="Log y", value=State.logy)
                    columns = list(map(str, df.get_column_names()))
                    sl.Select("Column x", values=columns, value=State.x)
                    sl.Select("Column y", values=columns, value=State.y)
                    sl.Select("Color", values=columns, value=State.color)

    if df is not None:
        if State.x.value is not None and State.y.value is not None:
            sl.FigurePlotly(
                px.scatter(
                    df,
                    State.x.value,
                    State.y.value,
                    color=State.color.value,
                    log_x=State.logx.value,
                    log_y=State.logy.value,
                    render_mode="webgl",
                ))
        else:
            sl.Warning("Select x and y columns")
    else:
        sl.Warning("No data loaded! Please upload a file.")
