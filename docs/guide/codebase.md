# Layout
The codebase folders are organized as follows:

```bash
├── __init__.py # python module requirement
├── assets # holds non-code assets, like help docs and images
│  └── help # in-app help blurbs/docs
├── pages # holds main pages and their components
│  ├── __init__.py
│  ├── components # all visual compoennts
│  │  ├── sidebar # all components which sit in the sidebar
│  │  └── views # plots things
│  ├── dataclass # dataclass objects
│  └── util # utility functions; initialized FIRST
└── vue # relevant vue files
```
