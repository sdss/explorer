import vaex as vx
import plotly.express as px
from plotly.graph_objs._figurewidget import FigureWidget

df = vx.example()  # Heelmi & de Zeeuw, 2000
z = df.count((df.x, df.y), shape=100, array_type="xarray")

# |%%--%%| <yKzJ5ofRhB|lRxo0TfykV>
r"""°°°
Works fine for standard Figure object.
°°°"""
# |%%--%%| <lRxo0TfykV|ldqIky4gnV>

fig = px.imshow(z.T)
fig.update_xaxes(autorange="reversed")

# |%%--%%| <ldqIky4gnV|9eMhlD6bsR>

fig.update_xaxes(autorange=True)

# |%%--%%| <9eMhlD6bsR|XFrMLraqUo>
r"""°°°
Now, trying with FigureWidget.
°°°"""
# |%%--%%| <XFrMLraqUo|8qYh0IIdFO>

fig_widget = FigureWidget(fig)
fig_widget.update_xaxes(autorange="reversed")

# |%%--%%| <8qYh0IIdFO|Gy6KUaQvBg>

fig_widget.update_xaxes(autorange=True)
