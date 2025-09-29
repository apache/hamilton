# Data Quality

Apache Hamilton has a simple but powerful data quality capability. This enables you to write functions
that have assertion on the output. For example...

```python
import pandas as pd
import numpy as np
from hamilton.function_modifiers import check_output

@check_output(
    data_type=np.int64,
    range=(0,100),
    importance="warn",
)
def some_int_data_between_0_and_100() -> pd.Series:
    pass
```

In the above, we run two assertions:

1. That the series has an np.int64 datatype
2. That every item in the series in between 0 and 100


Furthermore, the workflow does not fail when this dies. Rather, it logs a warning, as specified by the value provided to `importance`. In terms of how this works, if you were to visualize what was being executed (e.g. using `visualize_exection()`) then you'd see extra nodes added to the DAG. So when using `@check_output` an extra computational step will be added to your workflow to run that check.


## Design

To add data quality validation, we run an additional computational step in your workflow after function calculation.
See comments on the `BaseDataValidationDecorator` class for how it works.

## Default Validators

The available default validators are listed in the variable `AVAILABLE_DEFAULT_VALIDATORS`
in `default_validators.py`. To add more, please implement the class in that file then add to the list.
There is a test that ensures that everything is added to that list.

## Pandera Integration

We've fully integrated data quality with [pandera](https://pandera.readthedocs.io/en/stable/)!

Note that you have to have hamilton installed with the `pandera` extension. E.G.

```bash
pip install sf-hamilton[pandera]
```

The integration point is simple. All you have to do is provide a pandera schema
using the default data validator with argument `schema=`. This will validate the
output against a schema provided by you.

If you don't know what a pandera schema is or haven't worked with them before,
read more about it [here](https://pandera.readthedocs.io/en/stable/schema_models.html).
The integration works with schemas for both series and dataframes.

### Validating DataFrames

```python
import pandera as pa
import pandas as pd
from hamilton import function_modifiers

@function_modifiers.check_output(schema=pa.DataFrameSchema(
        {
            'column1': pa.Column(int),
            'column2': pa.Column(float, pa.Check(lambda s: s < -1.2)),
            # you can provide a list of validators
            'column3': pa.Column(str, [
                pa.Check(lambda s: s.str.startswith('value')),
                pa.Check(lambda s: s.str.split('_', expand=True).shape[1] == 2)
            ]),
        },
        index=pa.Index(int),
        strict=True,
    ))
def dataframe_with_schema(...) -> pd.DataFrame:
    ...
```

### Validating Series

```python
import pandera as pa
import pandas as pd
from hamilton import function_modifiers

@function_modifiers.check_output(schema = pa.SeriesSchema(
        str,
        checks=[
            pa.Check(lambda s: s.str.startswith('foo')),
            pa.Check(lambda s: s.str.endswith('bar')),
            pa.Check(lambda x: len(x) > 3, element_wise=True)
        ],
        nullable=False,
    ))
def series_with_schema(...) -> pd.Series:
    ...
```


You can also do schema checks on series, using the `pa.SeriesSchema` feature!

## Custom Validators

To add a custom validator, you need to implement the class `DataValidator`. You can then use the
`@check_output_custom` decorator to run it on a function. For example:

```python
import pandas as pd
import numpy as np

@check_output_custom(AllPrimeValidator(...))
def prime_number_generator(number_of_primes_to_generate: int) -> pd.Series:
    pass
```

## Urgency Levels

Currently there are two available urgency level:

1. "warn"
2. "fail"

They do exactly as you'd expect. "warn" logs the failure to the terminal and continues on. "fail"
raises an exception in the final node.

Limitations/future work are as follows:

1. Currently the actions are hardcoded. In the future, we will be considering adding
special actions for each level that one can customize...
2. One can only disable data quality checks by commenting out the decorator. We intend to allow node-specific overrides.
3. Currently the data quality results apply to every output of that function. E.G. if it runs `extract_columns`
it executes on every column that's extracted.

## Handling the results

We utilize tags to index nodes that represent data quality. All data-quality related tags start with the
prefix `hamilton.data_quality`. Currently there are two:

1. `hamilton.data_quality.contains_dq_results` -- this is a boolean that tells
whether a node outputs a data quality results. These are nodes that get injected when
a node is decorated, and can be queried by the end user.
2. `hamilton.data_quality.source_node` -- this contains the name of the source_node
the data to which the data quality points.

Note that these tags will not be present if the node is not related to data quality --
don't assume they're in every node.

To query one can simply filter for all the nodes that contain these tags and access the results!
