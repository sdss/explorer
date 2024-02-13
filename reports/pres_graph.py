import matplotlib.pyplot as plt
import mpl_preamble  # noqa
import numpy as np
import matplotlib as mpl
import scienceplots

mpl.use("pgf")

plt.style.use("science")
params = {
    "text.usetex": True,
    "pgf.texsystem": "pdflatex",
    "font.family": "serif",
    "font.serif": "",
    "legend.frameon": True,
    "figure.figsize": (7 / 2.54, 7 / 2.54),
}
plt.rcParams.update(params)

species = [f"DR{i}" for i in range(8, 18)] + ["DR19\n(projected)"]
datavols = [
    38.0,
    51.0,
    19.0,
    28.0,
    50.0,
    42.0,
    57.0,
    24.0,
    118.0,
    245.0,  # Dr17
    150 + 72,
]
cumulative = [0]
for vol in datavols[:-1]:
    cumulative.append(cumulative[-1] + vol)

weight_counts = {
    "Cumulative": np.array(cumulative),
    "New": np.array(datavols),
}
width = 0.5

fig, ax = plt.subplots(figsize=(10 / 2.54, 7 / 2.54))
bottom = 0

ax.grid(color="black", alpha=0.2, zorder=0)
bars = []
for boolean, weight_count in weight_counts.items():
    p = ax.bar(
        species,
        weight_count,
        width,
        label=boolean,
        bottom=bottom,
        edgecolor="black",
        alpha=1,
        zorder=25,
    )
    bars.append(p)
    bottom += weight_count
plt.xticks(fontsize=6)

heights = np.array(cumulative) + np.array(datavols)
for n, rect in enumerate(bars[0]):
    height = heights[n]
    plt.text(
        rect.get_x() + rect.get_width() / 2.0,
        height + 20,
        f"{height:.0f}",
        ha="center",
        va="bottom",
        zorder=50,
    )

ax.legend(loc="upper left")
ax.set_ylabel("Data Volume [TB]")
ax.set_xlabel("Data Release")
ax.set_ylim(0, 1e3)

plt.savefig("w9/images/datavolhist.pdf", dpi=500)
