r"""°°°
# Imports
°°°"""
# |%%--%%| <9YS5m6yxDR|4ttT4sizXs>

# Data
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', 500)

# Plotting
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import mpl_scatter_density

# Function
from tqdm import tqdm

# Galpy
from galpy.potential import MWPotential2014
# import plotting function for rotation curve
from galpy.potential import plotRotcurve
from galpy.orbit import Orbit

# Astropy
import astropy.units as u
from astropy.coordinates import SkyCoord, Galactic
from astropy.io import fits
from astropy.table import Table

# |%%--%%| <4ttT4sizXs|fSR4HJI2Io>
r"""°°°
# Data Aggregation
°°°"""
# |%%--%%| <fSR4HJI2Io|4k9DWJDCIb>

# Shortened version of AllStar containting members in NGC 2632
df = pd.read_csv("mwmAllStarAPOGEE_NGC_2632.csv")

# |%%--%%| <4k9DWJDCIb|MA43VVd9gB>

# Select only the dr17 spectra (this gets rid of duplicates between surveys)
df = df[(df.release == "dr17") & (~df.duplicated("sdss_id"))]

# |%%--%%| <MA43VVd9gB|mTbspuq7sh>

# Read in ASPCAP
aspcap = fits.open("../astraAllStarASPCAP-0.6.0.fits.gz")

# |%%--%%| <mTbspuq7sh|PG0R96WA2j>

# Only stars in the cluster
aspcap_bool = np.isin(aspcap[2].data['sdss_id'],
                      df.sdss_id) & (aspcap[2].data['release'] == "dr17")

# |%%--%%| <PG0R96WA2j|a92JaaiKhg>

# Read ASPCAP to an astropy Table
aspcap = Table(aspcap[2].data[aspcap_bool])

# |%%--%%| <a92JaaiKhg|DyST4LOmSX>

# Some sdss_ids were missing mwmStar v0.6.0 files
# This code aggregates the sdss_ids for which I found spectra
site = []
sdss_id = []
for i, row in tqdm(df.iterrows(), total=df.shape[0]):
    try:
        spec = fits.open(f"mwmStar-0.6.0-{row.sdss_id}.fits")
        if len(spec[3].data['wavelength']) > 0:
            site.append("APO")
            sdss_id.append(row.sdss_id)
        elif len(spec[4].data['wavelength']) > 0:
            site.append("LCO")
            sdss_id.append(row.sdss_id)
        else:
            continue

    except:
        continue

# |%%--%%| <DyST4LOmSX|PizLG1FzOB>

# This tests to make sure I'm not missing any astraStar files
for i, sid in enumerate(sdss_id):
    try:
        aspcap_spec = fits.open(f"astraStarASPCAP-0.6.0-{sid}.fits")
    except:
        print("Failed for:", sid)

# |%%--%%| <PizLG1FzOB|dIUycWYov5>

# Only select stars for which we have mwmStar files
df = df[np.isin(df.sdss_id, sdss_id)]

# |%%--%%| <dIUycWYov5|F9uLJsm81i>

# Convert aspcap to a pandas DataFrame and remove duplicates
names = [name for name in aspcap.colnames if len(aspcap[name].shape) <= 1]
aspcap_ = aspcap[names].to_pandas()
aspcap_ = aspcap_[~aspcap_.duplicated("sdss_id")]

# |%%--%%| <F9uLJsm81i|HUfwrIlmrG>

# make a new DataFrame containing the all the info we need
# This join also removes any aspcap stars not in the cluster
df_ = pd.merge(df,
               aspcap_[[
                   "sdss_id",
                   "teff",
                   "logg",
                   "m_h_atm",
                   "raw_teff",
                   "raw_logg",
                   "raw_m_h_atm",
               ]],
               left_on="sdss_id",
               right_on="sdss_id")
df_['absG'] = df_.g_mag + 5 * np.log10(df_.plx / 100)
df_['g_rp'] = df_.g_mag - df_.rp_mag

# |%%--%%| <HUfwrIlmrG|R0uor2dpIC>

# load mwmStar files in a list
loaded_files = [
    fits.open(f"mwmStar-0.6.0-{row.sdss_id}.fits")
    for i, row in df_.iterrows()
]

# |%%--%%| <R0uor2dpIC|YM3GKa4DSw>

# load StarASPCAP files into a list
loaded_aspcap = [
    fits.open(f"astraStarASPCAP-0.6.0-{row.sdss_id}.fits")[3]
    for i, row in df_.iterrows()
]

# |%%--%%| <YM3GKa4DSw|74idYoPRyg>

# Grab spectra from mwmStar
spectra = [
    loaded_files[i][3].data['flux'][0] for i in tqdm(range(len(loaded_files)))
]

# |%%--%%| <74idYoPRyg|3UB6yE0U0e>

# Grab NMF continuum from mwmStar
nmf_continuum = [
    loaded_files[i][3].data['continuum'][0]
    for i in tqdm(range(len(loaded_files)))
]

# |%%--%%| <3UB6yE0U0e|a9pX0TNgkS>

# Grab wavelengths from mwmStar
wavelengths = [
    loaded_files[i][3].data['wavelength']
    for i in tqdm(range(len(loaded_files)))
]

# |%%--%%| <a9pX0TNgkS|s4iYwKcVd8>

# Every wavelength solution is the same, so we only need the first one
wvl = wavelengths[0][0]

# |%%--%%| <s4iYwKcVd8|7ykGnzuzmr>

# Define the normalized spectra

# ASPCAP normalized
norm_spec = np.array([
    loaded_files[i][3].data['flux'][0] / loaded_aspcap[i].data['continuum'][0]
    for i in tqdm(range(len(loaded_files)))
])

# NMF normalized
norm_spec_nmf = np.array([
    loaded_files[i][3].data['flux'][0] /
    loaded_files[i][3].data['continuum'][0]
    for i in tqdm(range(len(loaded_files)))
])

# |%%--%%| <7ykGnzuzmr|GvlqEzp93e>

# Define the model spectra

#ASPCAP model flux
model_norm_spec = np.array([
    loaded_aspcap[i].data['model_flux'][0]
    for i in tqdm(range(len(loaded_files)))
])

# NMF model flux
model_norm_spec_nmf = np.array([
    loaded_files[i][3].data['nmf_rectified_model_flux'][0]
    for i in tqdm(range(len(loaded_files)))
])

# |%%--%%| <GvlqEzp93e|l1527K0lYZ>

# Orbits are fun
# Galpy ingestion
c_all = SkyCoord(ra=df_.ra.values * u.deg,
                 dec=df_.dec.values * u.deg,
                 distance=1000 / df_.plx.values * u.pc,
                 pm_ra_cosdec=df_.pmra.values * u.mas / u.yr,
                 pm_dec=df_.pmde.values * u.mas / u.yr,
                 radial_velocity=df_.v_rad.values * u.km / u.s)

# |%%--%%| <l1527K0lYZ|WBMk2xOL6k>

# Calculate orbits
o_all = Orbit(c_all, ro=8, vo=220)

# |%%--%%| <WBMk2xOL6k|SOccwnWQnS>

# Get angular momentum and radial action
df_['Lz'] = o_all.Lz(pot=MWPotential2014) / (8 * 220)
df_['jr'] = o_all.jr(pot=MWPotential2014) / (8 * 220)

# |%%--%%| <SOccwnWQnS|wCD6oAYUD5>
r"""°°°
# Plotting with bokeh
°°°"""
# |%%--%%| <wCD6oAYUD5|kX1ywwNkpS>

# Bokeh Imports
from bokeh.plotting import figure, output_file, curdoc, save
from bokeh.models import TapTool, HoverTool, ColumnDataSource, LinearColorMapper, CustomJS
from bokeh.layouts import gridplot, layout
from bokeh.io import output_file, show
from bokeh.util.hex import hexbin
from bokeh.transform import log_cmap
from bokeh.palettes import Greys256
from bokeh.models import ColorBar

# Plot Global Pars
fullwidth = 800

##############################
### Create the Kiel figure ###
##############################

# Bokeh functions by first defining the plots, then adding tools,
# and finally putting everything together. Here, we define the
# Kiel diagram figure.

pkiel = figure(title=f'Members of NGC 2632 \n Raw ASPCAP 0.6.0',
               height=250,
               width=int(fullwidth / 3),
               sizing_mode='scale_both',
               x_range=(9000, 2500),
               y_range=(6.1, 2.5),
               tools="pan,wheel_zoom,box_zoom,reset",
               min_border=10,
               min_border_left=50,
               min_border_right=50,
               toolbar_location="above",
               border_fill_color="whitesmoke")
# Rid myself of the bokeh logo
pkiel.toolbar.logo = None
# Label axes
pkiel.xaxis.axis_label = 'Raw Teff'
pkiel.yaxis.axis_label = 'Raw logg'

print("adding scatter plot")

# Define a colormap (this one maps to ASPCAP's raw [M/H])
exp_cmap = LinearColorMapper(palette="BuRd9",
                             low=np.quantile(df_.raw_m_h_atm, 0.01),
                             high=np.quantile(df_.raw_m_h_atm, 0.99))

# Add the scatter data to the Kiel figure
# These are stagnant data that will not move
scat = pkiel.scatter(
    x='raw_teff',
    y='raw_logg',
    source=df_[['raw_teff', 'raw_logg', 'raw_m_h_atm', 'sdss_id']],
    size=16,
    fill_color={
        "field": "raw_m_h_atm",
        "transform": exp_cmap
    })

# Next, we add a red highlight point that will move around the Kiel diagram
# It _has_ to be a ColumnDataSource so that it can be updated in the JavaScript

# This line adds the data (just select the first row in the list)
point_kiel_red = ColumnDataSource(
    dict(x=[df_.raw_teff.iloc[0]], y=[df_.raw_logg.iloc[0]]))
# This line plots it on the figure
scat_kiel_red = pkiel.scatter("x",
                              "y",
                              source=point_kiel_red,
                              size=20,
                              fill_color="red")

# Finally, we give the figure a colorbar
bar = ColorBar(color_mapper=exp_cmap,
               location=(0, 0),
               title="Raw Atmospheric [M/H]")
pkiel.add_layout(bar, "left")

#############################
### Create the CMD figure ###
#############################

# Now make the CMD diagram plot
pcmd = figure(title="Gaia DR3 CMD",
              height=250,
              width=int(fullwidth / 3),
              sizing_mode='scale_both',
              x_range=(-0.1, 1.5),
              y_range=(15, -1),
              tools="pan,wheel_zoom,box_zoom,reset",
              min_border=10,
              min_border_left=50,
              min_border_right=50,
              toolbar_location="above",
              border_fill_color="whitesmoke")

# Add the stagnant CMD scatter points
scat_cmd = pcmd.scatter(x='g_rp',
                        y="absG",
                        source=df_[['g_rp', 'absG', 'raw_m_h_atm', "sdss_id"]],
                        size=16,
                        fill_color={
                            "field": "raw_m_h_atm",
                            "transform": exp_cmap
                        })

# Add the highlight point
point_cmd_red = ColumnDataSource(
    dict(x=[df_.g_rp.iloc[0]], y=[df_.absG.iloc[0]]))
scat_cmd_red = pcmd.scatter("x",
                            "y",
                            source=point_cmd_red,
                            size=20,
                            fill_color="red")

# Plot attributes
pcmd.toolbar.logo = None
pcmd.xaxis.axis_label = 'G-RP'
pcmd.yaxis.axis_label = 'Absolute G Magnitude'

###############################
### Create the Orbit figure ###
###############################

# Orbit scatter_plot
p_orbit = figure(title="Orbit Kinematics",
                 height=250,
                 width=int(fullwidth / 3),
                 sizing_mode='scale_both',
                 x_range=(np.quantile(df_.Lz, 0.01), np.quantile(df_.Lz,
                                                                 0.99)),
                 y_range=(np.quantile(df_.jr, 0.01), np.quantile(df_.jr,
                                                                 0.99)),
                 tools="pan,wheel_zoom,box_zoom,reset",
                 min_border=10,
                 min_border_left=50,
                 min_border_right=50,
                 toolbar_location="above",
                 border_fill_color="whitesmoke")
# Stagnant orbit points (you get the picture)
scat_orbit = p_orbit.scatter(x="Lz",
                             y="jr",
                             source=df_[["jr", "Lz", "raw_m_h_atm",
                                         "sdss_id"]],
                             size=16,
                             fill_color={
                                 "field": "raw_m_h_atm",
                                 "transform": exp_cmap
                             })

point_orbit_red = ColumnDataSource(dict(x=[df_.Lz.iloc[0]],
                                        y=[df_.jr.iloc[0]]))
scat_orbit_red = p_orbit.scatter("x",
                                 "y",
                                 source=point_orbit_red,
                                 size=20,
                                 fill_color="red")

p_orbit.toolbar.logo = None
p_orbit.xaxis.axis_label = 'Angular Momentum L_z [8kpc x 220 km/s]'
p_orbit.yaxis.axis_label = 'Radial Action J_r [8kpc x 220 km/s]'

#################################
### Create the Spectrum Plots ###
#################################

# Define a simple hover tool for the spectrum plots
shover = HoverTool(tooltips=[
    ("(λ,L)", "($x, $y)"),
])

#######################
### ASPCAP spectrum ###
#######################

# Make the spectra plot, include the hover in 'tools'
# Don't ask why the plot is called 'ph'
ph = figure(
    title=
    "APOGEE DR17 Spectrum SDSS-V v0.6.0 Reduction (ASPCAP continuum normalized) : Black = Spectrum , Red = ASPCAP Model",
    toolbar_location="above",
    width=fullwidth,
    height=100,
    min_border=50,
    min_border_left=50,
    y_axis_location="left",
    tools=[shover, "pan,wheel_zoom,box_zoom,reset"],
    y_range=(0, 1.3))

# Various settings
ph.xgrid.grid_line_color = None
ph.yaxis.major_label_orientation = np.pi / 4
ph.background_fill_color = "#fafafa"
ph.sizing_mode = 'scale_both'
ph.xaxis.axis_label = "Wavelength (Å)"
ph.yaxis.axis_label = "Rectified Flux"

# Add the spectrum data to a ColumnDataSource
spectrum = ColumnDataSource(dict(x=wvl, y=norm_spec[0]))
# Plot the ColumnDataSource on the spectrum plot
spec_plt = ph.line("x", "y", source=spectrum, line_color="black")

# Same for the model spectrum but make it red
model = ColumnDataSource(dict(x=wvl, y=model_norm_spec[0]))
mod_plt = ph.line("x", "y", source=model, line_color="red")

####################
### NMF spectrum ###
####################

# Second verse, same as the first
ph_nmf = figure(
    title=
    "APOGEE DR17 Spectrum SDSS-V v0.6.0 Reduction (NMF continuum normalized) : Black = Spectrum , Red = NMF Model",
    toolbar_location="above",
    width=fullwidth,
    height=100,
    min_border=50,
    min_border_left=50,
    y_axis_location="left",
    tools=[shover, "pan,wheel_zoom,box_zoom,reset"],
    y_range=(0, 1.3))

# Various settings
ph_nmf.xgrid.grid_line_color = None
ph_nmf.yaxis.major_label_orientation = np.pi / 4
ph_nmf.background_fill_color = "#fafafa"
ph_nmf.sizing_mode = 'scale_both'
ph_nmf.xaxis.axis_label = "Wavelength (Å)"
ph_nmf.yaxis.axis_label = "Rectified Flux"

spectrum_nmf = ColumnDataSource(dict(x=wvl, y=norm_spec_nmf[0]))
spec_nmf_plt = ph_nmf.line("x", "y", source=spectrum_nmf, line_color="black")

model_nmf = ColumnDataSource(dict(x=wvl, y=model_norm_spec_nmf[0]))
mod_nmf_plt = ph_nmf.line("x", "y", source=model_nmf, line_color="red")

#############################
### JavaScript Hover Tool ###
#############################

print("adding hover active")

# Below is the JavaScript code that is executed on each callback
# Important things to note here:
# 1) the .emit() calls might not be strictly necessary, I don't actually know
# 2) all updates to a ColumnDataSource must be arrays (in square brackets), even if it is a single datum
# 3) hoveractive must be set to True at the beginning of the callback, otherwise nothing ever triggers
# 4) bokeh will flatten all of your data into 1D. So plan accordingly
#       -- see where I set source.data.y to span an APOGEE spectrum
# 5) you can hunt for bugs by printing variables using 'console.log(foo)' in the JavaScript
#       -- BUT this will print to the browser console, not in python

code = '''
const ind = cb_data.index.indices.slice(-1)[0];
if (hoveractive && ind != undefined) {
    source.data.y = spectra.slice(ind*8575, (ind+1)*8575);
    source.change.emit();
    msource.data.y = mods.slice(ind*8575, (ind+1)*8575);
    msource.change.emit();
    
    source_nmf.data.y = spectra_nmf.slice(ind*8575, (ind+1)*8575);
    source_nmf.change.emit();
    msource_nmf.data.y = mods_nmf.slice(ind*8575, (ind+1)*8575);
    msource_nmf.change.emit();
    
    cmd_red.data.x = [cmd_g_rp[ind]];
    cmd_red.data.y = [cmd_absG[ind]];
    cmd_red.change.emit();
    
    kiel_red.data.x = [kiel_teff[ind]];
    kiel_red.data.y = [kiel_logg[ind]];
    kiel_red.change.emit();
    
    orbit_red.data.x = [orbit_Lz[ind]];
    orbit_red.data.y = [orbit_jr[ind]];
    orbit_red.change.emit();
}
'''

# Define the callback and include the python variables that get passed to it
callback = CustomJS(
    args={
        'hoveractive': True,
        'sdss_id': df_.sdss_id,

        # ASPCAP spectrum data
        'spectra': norm_spec,
        'mods': model_norm_spec,
        'source': spec_plt.data_source,
        'msource': mod_plt.data_source,

        # NMF spectrum data
        'spectra_nmf': norm_spec_nmf,
        'mods_nmf': model_norm_spec_nmf,
        'source_nmf': spec_nmf_plt.data_source,
        'msource_nmf': mod_nmf_plt.data_source,

        # CMD data
        'cmd_red': scat_cmd_red.data_source,
        'cmd_g_rp': df_.g_rp,
        'cmd_absG': df_.absG,

        # Kiel data
        'kiel_red': scat_kiel_red.data_source,
        'kiel_teff': df_.raw_teff,
        'kiel_logg': df_.raw_logg,

        # Orbit data
        'orbit_red': scat_orbit_red.data_source,
        'orbit_Lz': df_.Lz,
        'orbit_jr': df_.jr,
    },
    code=code)

# Make a hover tool that uses the callback we defined
# Make sure to include which plots can render the callback
# In this instance, this is is the CMD, Orbit, and Kiel plots
# Also, 'tooltips' displays the sdss_id when a point is hovered on
hover = HoverTool(tooltips=[("sdss_id", "@sdss_id")],
                  callback=callback,
                  renderers=[scat_cmd, scat_orbit, scat])
# ^ it is worht including that this line is where you would edit things
# about your interaction with the plot. E.g. do you want a clicking tool instead?
# Or maybe a smaller hover radius?

# Add the custom hover tool to the plots
pkiel.add_tools(hover)
pcmd.add_tools(hover)
p_orbit.add_tools(hover)

print("making layout")

# Add plots to a big layout
# The location of each plot is dictated here in a 2D list
# pkiel, p_orbit, and pcmd are in the first row but in separate columns
layout_ = layout([[pkiel, p_orbit, pcmd], [ph], [ph_nmf]],
                 sizing_mode='scale_both')

# Honestly, no idea what this does
curdoc().add_root(layout_)

# Save the interactive plot to a file
print("saving output")
output_file(filename="ngc_2632_viz_raw_aspcap_w_NMF.html")
save(layout_)

# Use this to automatically pull up the plot when it's made
#show(layout)
