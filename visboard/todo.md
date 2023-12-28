**fix the damn autoloading of multiple (2 loaders generated, dont want first)**

**add func to convert ( a < X < b) to (a < x) & (X < b)**
  - vaex's expression doesn't support this type of expression, need to translate it.

**fix the crash on unloading dataset**
- this might be low priority, but i think its important to figure out why it crashes when the amount of renders is reduced in the way i've implemented it on the sidebar
- specifically crashes in hist2d*

**add subset functionality**
