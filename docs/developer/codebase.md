# Layout
The codebase folders are organized as follows:

```bash
├── docs
│  ├── assets # documentation assets
│  ├── developer # developer handbook
│  ├── examples # examples
│  ├── javascripts # javascript source for docs
│  └── user # user guides
├── scripts # holds a doc generation script
└── src
  └── sdss_explorer
      ├── __pycache__
      ├── assets # non-code assets, like help blurbs/docs
      │  └── help # help menus
      ├── dashboard # the dashboard
      │  ├── components # all visual components
      │  │  ├── sidebar # all components that live in the sidebar
      │  │  └── views # plot views
      │  └── dataclass # dataclass objects and namespaces
      ├── server # custom summary file backend server
      ├── util # utility functions, common across all apps
      └── vue # some misc vue
```
