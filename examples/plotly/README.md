# Plotly materializer extension

By importing `hamilton.plugins.plotly_extensions`, you can register two additional materializers for Plotly figures. The `to.plotly()` creates static image files ([docs](https://plotly.com/python/static-image-export/)) and the `to.html()` outputs interactive HTML files ([docs](https://plotly.com/python/interactive-html-export/)).

## How to
You need to install `plotly` (low-level API) to annotate your function with `plotly.graph_objects.Figure` even if you are using `plotly_express` (high-level API) to generate figures.
```python
# 1. define a function returning a `plotly.graph_objects.Figure` in a python module.
def confusion_matrix(...) -> plotly.graph_objects.Figure:
    return plotly.express.imshow(...)

# 2. import the module and create the Apache Hamilton driver
dr = (
    driver.Builder()
    .with_config({...})
    .with_modules(MODULE_NAME)
    .build()
)

# 3. define the materializers
from hamilton.io.materialization import to

materializers = [
    to.plotly(
        dependencies=["confusion_matrix_figure"],
        id="confusion_matrix_png",
        path="./static.png",
    ),
    to.html(
        dependencies=["confusion_matrix_figure"],
        id="confusion_matrix_html",
        path="./interactive.html",
    ),
]

# 4. materialize figures
dr.materialize(*materializers)
```

## Notes
Here are a few things to consider when using the plotly materializers:
- Any plotly figure is a subclass of `plotly.graph_objects.Figure`, including anything from `plotly.express`, `plotly.graph_objects`, `plotly.figure_factory`.
- `to.plotly()` supports all filetypes of the plotly rendering engine (PNG, SVG, etc.). The output type will be automatically inferred from the `path` value passed to the materializer. Or, you can specify the file type explicitly as `kwarg`.
- `to.html()` outputs an interactive HTML file. These files will be at least ~3Mb each since they include they bundle the plotly JS library. You can reduce that by using the `include_plotlyjs` `kwarg`. Read more about it in the documentation at `https://plotly.com/python/interactive-html-export/`
- `to.html()` will include the data that's being visually displayed, including what's part of the tooltips, which can grow filesize quickly.
