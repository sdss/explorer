# LOADERS
**fix the damn autoloading of multiple (2 loaders generated, dont want first)**
  - dont know what to do about this


# SOLARA VAEX

## FEATURES

**FEATURE: log colorscale**

**FEAT: download via context menu on scatterplots**
for download: needs which ipl and which id (very easy)
'
**FEAT: jdaviz via context menu**
on another server, prestarted for a demo with a temp spectra

**feat: add subset functionality**
- i.e, the ability to add multiple expression sets and toggle them on and off

***FEATURE: add selection to histogram and skyplot***

**CORE FEATURE: application settings in top right**

add route to jdaviz (find out how to)

give singularity and docker a whirl

add multi-dataset functionality (long term)

***DEPLOYMENT ON UTAH***
make a singularity.
the utah VM is free from feb 15

** MIHT BE ABLE TO ADD RESIZE VIA THE RESIZE CALLBACK OF THE GRID ITEM OBJECTS I NTHE VUE GRID LAYOUYT**


**ADD routes to diff datasets (only changes state file) and loading properties**

**LOFTY GOAL:** make a wiki clone of the confluence for a local running host via xwiki

# make filters clear when it is derendered

## andy suggestions

create parquet for 2 other pipes (ASPCAP, The Cannon)

styling

deployment on singularity applet thingy



## FIXES
**fix: crash on hook issues**
  - there are some condition hooks in plotting functions that need to be sorted out else the app will crash due to hook mismanagement every time a plot is say del'd from rendering

**make the plots automatically resize**
  - plotly makes me want to go jump into a lake
  - out of scope someone else do it for me

***FIX: relayout bugging when any axes are logarithmic or flipped***

## LOFTY GOALS



**REALLY HARD TO IMPLEMENT FEATURE: scatterplot relayout adaptive rerendering underlying trace**
  - there is a max the browser can render, say 5k
  - when the layout changes, change the subset being shown and update with a new one according to what can be visible on-screen.
  - this is implemented, but when you pan, its janky because not everything is shown
  - i want to implement say a soft heatmap trace beneath the scatter points outside the shown range or vice versa to give indications of density.
    **heatmap skyplot?**
      - doesn't seem like there's a trace for one

# 
