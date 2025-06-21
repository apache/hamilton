# Allowing modules to override same named functions

When constructing the ``Driver``, we can import several modules:

```python
from hamilton import driver
import module_A
import module_B

dr = (
    driver.Builder()
    .with_modules(module_A, module_B)
)
```

Now, it can happen that ``module_A`` and ``module_B`` both have a python function with the same name but performing different things:

```python
# module_A
import pandas as pd

def weighted_average(data:pd.Series, weight:int)->pd.Series:
    return weight*data.mean()
```

```python
# module_B
import pandas as pd

def weighted_average(data:pd.Series, weight:int)->pd.Series:
    return data.mean() / weight
```


In this case Apache Hamilton will raise an error since we cannot have two same named functions in the DAG.

We have a handy flag for you to allow the later imported module to overwrite the previous same-named functions:

```python
dr = (
    driver.Builder()
    .with_modules(module_A, module_B)
    .allow_module_overrides()
)
```

which will tell Apache Hamilton to use ``module_B.weighted_average()`` for the node and ignore the same-named function from ``module_A``.
