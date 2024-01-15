**fix the damn autoloading of multiple (2 loaders generated, dont want first)**

**add func to convert ( a < X < b) to (a < x) & (X < b)**
  - vaex's expression doesn't support this type of expression, need to translate it.

**fix the crash on unloading dataset**
- this might be low priority, but i think its important to figure out why it crashes when the amount of renders is reduced in the way i've implemented it on the sidebar
- specifically crashes in hist2d*

**add subset functionality**

**make the plots automatically resize**

**prevent rerender when only light dependencies are updated (i.e, layout, etc)**

**assertion error message information (except as e, assert cond, info)**

***FIX: except the click and hold events when over the plotly object (somehow)***

**CORE FEATURE: quick filters (i.e. all flags zero, high snr, certain telescope subsets, etc)**

**CORE FEATURE: allow for further input order variety in expreditor**
  - 3 part expressions dont work currently, must be converted.
  - 2 part expression in any order (i.e., make it so 1500 < teff and teff > 1500 can be input.)
  **allow for catagorical comparisons in expreditor**
  **allow for equality/inequality comparisons in expreditor**

**CORE FEATURE: application settings in top right**

**heatmap skyplot? (as opposed)**

**REALLY HARD TO IMPLEMENT FEATURE: scatterplot relayout adaptive rerendering**
  - there is a max the browser can render, say 5k
  - when the layout changes, change the subset being shown and update with a new one according to what can be visible on-screen.
