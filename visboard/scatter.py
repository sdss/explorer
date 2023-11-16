"""
Interactive scatter plot testing

"""
import vaex as vx
import solara as sl
from matplotlib.figure import Figure

# dataframe loader
df = vx.example()

# @sl.component
# def x_y_selector():
#    x = sl.use_reactive("TEFF")
#    y = sl.use_reactive("LOGG")
#    sl.Select(label="X axis", values=keys, value=x)
#    sl.Select(label="Y axis", values=keys, value=y)
#    return x, y


@sl.component
def Page():
    keys = df.get_column_names()
    x = sl.use_reactive("x")
    y = sl.use_reactive("y")
    fig = Figure()
    ax = fig.subplots()
    ax.scatter(df[x.value].values, df[y.value].values)
    with sl.Column() as main:
        sl.Select(label="X axis", values=keys, value=x)
        sl.Select(label="Y axis", values=keys, value=y)
        sl.FigureMatplotlib(fig)
    return main
