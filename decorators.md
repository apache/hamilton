# Decorators

While the 1:1 mapping of column -> function implementation is powerful, we've implemented a few decorators to promote
business-logic reuse. The decorators we've defined are as follows
(source can be found in [function_modifiers](hamilton/function_modifiers.py)):

## @parameterize
Expands a single function into n, each of which correspond to a function in which the parameter value is replaced either by:
1. A specified value
2. The value from a specified upstream node.

Note that this can take the place of any of the `@parameterize` decorators below. In fact, they delegate to this!

```python
import pandas as pd
from hamilton.function_modifiers import parameterize
from hamilton.function_modifiers import value, source


@parameterize(
    D_ELECTION_2016_shifted=dict(n_off_date=source('D_ELECTION_2016'), shift_by=value(3)),
    SOME_OUTPUT_NAME=dict(n_off_date=source('SOME_INPUT_NAME'), shift_by=value(1)),
)
def date_shifter(n_off_date: pd.Series, shift_by: int = 1) -> pd.Series:
    """{one_off_date} shifted by shift_by to create {output_name}"""
    return n_off_date.shift(shift_by)
```

By choosing `literal` or `upstream`, you can determine the source of your dependency. Note that you can
also pass documentation. If you don't, it will use the parameterized docstring.

```python
@parameterize(
    D_ELECTION_2016_shifted=(dict(n_off_date=source('D_ELECTION_2016'), shift_by=value(3)), "D_ELECTION_2016 shifted by 3"),
    SOME_OUTPUT_NAME=(dict(n_off_date=source('SOME_INPUT_NAME'), shift_by=value(1)),"SOME_INPUT_NAME shifted by 1")
)
def date_shifter(n_off_date: pd.Series, shift_by: int=1) -> pd.Series:
    """{one_off_date} shifted by shift_by to create {output_name}"""
    return n_off_date.shift(shift_by)
```



## @parameterize_values (replacing @parametrized)
Expands a single function into n, each of which corresponds to a function in which the parameter value is replaced by
that *specific value*.
```python
import pandas as pd
from hamilton.function_modifiers import parameterize_values
import internal_package_with_logic

ONE_OFF_DATES = {
     #output name        # doc string               # input value to function
    ('D_ELECTION_2016', 'US Election 2016 Dummy'): '2016-11-12',
    ('SOME_OUTPUT_NAME', 'Doc string for this thing'): 'value to pass to function',
}
            # parameter matches the name of the argument in the function below
@parameterize_values(parameter='one_off_date', assigned_output=ONE_OFF_DATES)
def create_one_off_dates(date_index: pd.Series, one_off_date: str) -> pd.Series:
    """Given a date index, produces a series where a 1 is placed at the date index that would contain that event."""
    one_off_dates = internal_package_with_logic.get_business_week(one_off_date)
    return internal_package_with_logic.bool_to_int(date_index.isin([one_off_dates]))
```
We see here that `parameterized` allows you keep your code DRY by reusing the same function to create multiple
distinct outputs. The _parameter_ key word argument has to match one of the arguments in the function. The rest of
the arguments are pulled from outside the DAG. The _assigned_output_ key word argument takes in a dictionary of
tuple(Output Name, Documentation string) -> value.

Note that `@parametrized` is deprecated, and we intend for you to use `@parameterize_vales`. We're consolidating
to make the parameterization decorators more consistent! You have plenty of time to migrate,
we wont make this a hard change until we have a Apache Hamilton 2.0.0 to release.


## @parameterize_sources (replacing @parameterized_inputs)

Expands a single function into _n_, each of which corresponds to a function in which the parameters specified are mapped
to the specified inputs. Note this decorator and `@parameterize_values` are quite similar, except that
the input here is another DAG node(s), i.e. column/input, rather than a specific scalar/static value.

```python
import pandas as pd
from hamilton.function_modifiers import parameterize_sources


@parameterize_sources(
    D_ELECTION_2016_shifted=dict(one_off_date='D_ELECTION_2016'),
    SOME_OUTPUT_NAME=dict(one_off_date='SOME_INPUT_NAME')
)
def date_shifter(one_off_date: pd.Series) -> pd.Series:
    """{one_off_date} shifted by 1 to create {output_name}"""
    return one_off_date.shift(1)

```
We see here that `parameterize_sources` allows you to keep your code DRY by reusing the same function to create multiple
distinct outputs. The key word arguments passed have to have the following structure:
> OUTPUT_NAME = Mapping of function argument to input that should go into it.

So in the example, `D_ELECTION_2016_shifted` is an _output_ that will correspond to replacing `one_off_date` with `D_ELECTION_2016`.
Then similarly `SOME_OUTPUT_NAME` is an _output_ that will correspond to replacing `one_off_date` with `SOME_INPUT_NAME`.
The documentation for both uses the same function doc and will replace values that are templatized with the input
parameter names, and the reserved value `output_name`.

To help visualize what the above is doing, it is equivalent to writing the following two function definitions:

```python
def D_ELECTION_2016_shifted(D_ELECTION_2016: pd.Series) -> pd.Series:
    """D_ELECTION_2016 shifted by 1 to create D_ELECTION_2016_shifted"""
    return D_ELECTION_2016.shift(1)

def SOME_OUTPUT_NAME(SOME_INPUT_NAME: pd.Series) -> pd.Series:
    """SOME_INPUT_NAME shifted by 1 to create SOME_OUTPUT_NAME"""
    return SOME_INPUT_NAME.shift(1)
```
Note that `@parameterized_inputs` is deprecated, and we intend for you to use `@parameterize_sources`. We're consolidating
to make the parameterization decorators more consistent! But we will not break your workflow for a long time.

*Note*: that the different input variables must all have compatible types with the original decorated input variable.

## Migrating @parameterized*

As we've said above, we're planning on deprecating the following:

- `@parameterized_inputs` (replaced by `@parameterize_sources`)
- `@parametrized` (replaced by `@parameterize_values`, as that's what its really doing)
- `@parametrized_input` (deprecated long ago, migrate to `@parameterize_sources` as that is more versatile.)

In other words, we're aligning around the following `@parameterize` implementations:

- `@parameterize` -- this does everything you want
- `@parameterize_values` -- this just changes the values, does not change the input source
- `@parameterize_sources`-- this just changes the source of the inputs. We also changed the name from inputs -> sources as it was clearer (values are inputs as well).

The only non-drop-in change you'll have to do is for `@parameterized`. We won't update this until `hamilton==2.0.0`, though,
so you'll have time to migrate for a while.


## @extract_columns
This works on a function that outputs a dataframe, that we want to extract the columns from and make them individually
available for consumption. So it expands a single function into _n functions_, each of which take in the output dataframe
 and output a specific column as named in the `extract_columns` decorator.
```python
import pandas as pd
from hamilton.function_modifiers import extract_columns

@extract_columns('fiscal_date', 'fiscal_week_name', 'fiscal_month', 'fiscal_quarter', 'fiscal_year')
def fiscal_columns(date_index: pd.Series, fiscal_dates: pd.DataFrame) -> pd.DataFrame:
    """Extracts the fiscal column data.
    We want to ensure that it has the same spine as date_index.
    :param fiscal_dates: the input dataframe to extract.
    :return:
    """
    df = pd.DataFrame({'date_index': date_index}, index=date_index.index)
    merged = df.join(fiscal_dates, how='inner')
    return merged
```
Note: if you have a list of columns to extract, then when you call `@extract_columns` you should call it with an
asterisk like this:
```python
import pandas as pd
from hamilton.function_modifiers import extract_columns

@extract_columns(*my_list_of_column_names)
def my_func(...) -> pd.DataFrame:
   """..."""
```

## @does
`@does` is a decorator that allows you to replace the decorated function with the behavior from another
function. This allows for easy code-reuse when building repeated logic. You do this by decorating a
function with`@does`, which takes in two parameters:
1. `replacing_function` Required -- a function that takes in a "compatible" set of arguments. This means that it
will work when passing the corresponding keyword arguments to the decorated function.
2. `**argument_mapping` -- a mapping of arguments from the replacing function to the replacing function. This makes for easy reuse of
functions. Confused? See the examples below.

```python
import pandas as pd
from hamilton.function_modifiers import does

def _sum_series(**series: pd.Series) -> pd.Series:
    """This function takes any number of inputs and sums them all together."""
    return sum(series)

@does(_sum_series)
def D_XMAS_GC_WEIGHTED_BY_DAY(D_XMAS_GC_WEIGHTED_BY_DAY_1: pd.Series,
                              D_XMAS_GC_WEIGHTED_BY_DAY_2: pd.Series) -> pd.Series:
    """Adds D_XMAS_GC_WEIGHTED_BY_DAY_1 and D_XMAS_GC_WEIGHTED_BY_DAY_2"""
    pass
```

In the above example `@does` applies `_sum_series` to the function `D_XMAS_GC_WEIGHTED_BY_DAY`.
Note we don't need any parameter replacement as `_sum_series` takes in just `**kwargs`, enabling it
to work with any set of parameters (and thus any old function).

```python
import pandas as pd
from hamilton.function_modifiers import does

import internal_company_logic

def _load_data(db: str, table: str) -> pd.DataFrame:
    """Helper function to load data using your internal company logic"""
    return internal_company_logic.read_table(db=db, table=table)

@does(_load_data, db='marketing_spend_db', table='marketing_spend_table')
def marketing_spend_data(marketing_spend_db: str, marketing_spend_table: str) -> pd.Series:
    """Loads marketing spend data from the database"""
    pass

@does(_load_data, db='client_acquisition_db', table='client_acquisition_table')
def client_acquisition_data(client_acquisition_db: str, client_acquisition_table: str) -> pd.Series:
    """Loads client acquisition data from the database"""
    pass
```

In the above example, `@does` applies our internal function `_load_data`, which applies custom
logic to load a table from a database in the data warehouse. Note that we map the parameters -- in the first example,
the value of the parameter `marketing_spend_db` is passed to `db`, and the value of the parameter `marketing_spend_table`
is passed to `table`.


## @config.when*

`@config.when` allows you to specify different implementations depending on configuration parameters.

The following use cases are supported:
1. A column is present for only one value of a config parameter -- in this case, we define a function only once,
   with a `@config.when`
```python
    import pandas as pd
    from hamilton.function_modifiers import config

    # signups_parent_before_launch is only present in the kids business line
    @config.when(business_line='kids')
    def signups_parent_before_launch(signups_from_existing_womens_tf: pd.Series) -> pd.Series:
        """TODO:
        :param signups_from_existing_womens_tf:
        :return:
        """
        return signups_from_existing_womens_tf
```
2. A column is implemented differently for different business inputs, e.g. in the case of Stitch Fix gender intent.
```python
    import pandas as pd
    from hamilton.function_modifiers import config, model
    import internal_package_with_logic

    # Some 21 day autoship cadence does not exist for kids, so we just return 0s
    @config.when(gender_intent='kids')
    def percent_clients_something__kids(date_index: pd.Series) -> pd.Series:
        return pd.Series(index=date_index.index, data=0.0)

    # In other business lines, we have a model for it
    @config.when_not(gender_intent='kids')
    @model(internal_package_with_logic.GLM, 'some_model_name', output_column='percent_clients_something')
    def percent_clients_something_model() -> pd.Series:
        pass
```
Note the following:
- The function cannot have the same name in the same file (or python gets unhappy), so we name it with a
  __ (dunderscore) as a suffix. The dunderscore is removed before it goes into the DAG.
- There is currently no `@config.otherwise(...)` decorator, so make sure to have `config.when` specify set of
  configuration possibilities.
Any missing cases will not have that output column (and subsequent downstream nodes may error out if they ask for it).
To make this easier, we have a few more `@config` decorators:

    - `@config.when_not(param=value)` Will be included if the parameter is _not_ equal to the value specified.
    - `@config.when_in(param=[value1, value2, ...])` Will be included if the parameter is equal to one of the specified
      values.
    - `@config.when_not_in(param=[value1, value2, ...])` Will be included if the parameter is not equal to any of the
      specified values.
    - `@config` If you're feeling adventurous, you can pass in a lambda function that takes in the entire configuration
      and resolves to
    `True` or `False`. You probably don't want to do this.

To pass in the right value, you would provide `param`, e.g. `gender_intent`, or `business_line`, as a field in the dictionary passed to instantiate the driver. E.g.
```python
config = {
  "business_line": "kids"
}
dr = driver.Driver(config, module1, ...)
```

## @tag and friends

### @tag

Allows you to attach metadata to an output(s), i.e. all nodes generated by a function and its decorators (note, this, by default, only applies to "final" nodes --
not any intermediate nodes that are generated...). See "A mental model for decorators" below for how/why this works.

A common use of this is to enable marking nodes as part of some data product, or for GDPR/privacy purposes.

For instance:

```python
import pandas as pd
from hamilton.function_modifiers import tag

def intermediate_column() -> pd.Series:
    pass

@tag(data_product='final', pii='true')
def final_column(intermediate_column: pd.Series) -> pd.Series:
    pass
```

`@tag` also allows you to specify a target with the `target_` parameter. See "A mental model for decorators" below for more details.


### @tag_outputs (deprecated)

`tag_outputs` enables you to attach metadata to a function that outputs multiple nodes,
and give different tag values to different outputs:

```python
import pandas as pd
from hamilton.function_modifiers import tag_outputs, extract_columns

def intermediate_column() -> pd.Series:
    pass

@tag_outputs(
    public={'column_a' : 'public'},
    private={'column_b' : 'private'})
@extract_columns('column_a', 'column_b')
def data_used_in_multiple_ways() -> pd.DataFrame:
    return load_some_data(...)
```

In this case, the tag `accessibility` would have different values for the two nodes produced by the `data_used_in_multiple_ways`
function -- `public` for `column_a` public `private` for `column_b`..

A note on decorator precedence. If using `@tag` together with `@tag_outputs` on a function (you might want to do this because you use `@tag` to
"tag" all nodes with a certain set of values, and `@tag_outputs` to "tag" specific outputs with specific values),
they will be applied in order up from the function. So if you desire to override
`@tag`, for that to work, you would put `tag_outputs` above `tag` (as it would be applied last).

```python
import pandas as pd
from hamilton.function_modifiers import tag_outputs, tag, extract_columns

def intermediate_column() -> pd.Series:
    pass

@tag_outputs(
    public={'column_a' : 'public'},
    private={'column_b' : 'private', 'common_tag' : 'bar'})
@tag(common_tag="foo")
@extract_columns('column_a', 'column_b')
def data_used_in_multiple_ways() -> pd.DataFrame:
    return load_some_data(...)
```

In the case above, `common_tag` would resolve to `foo` for `column_a` and `bar` for `column_b`.
Attempting an override in the reverse direction is currently undefined behavior.

### How do I query by tags?
Right now, we don't have a specific interface to query by tags, however we do expose them via the driver.
Using the `list_available_variables()` capability exposes tags along with their names & types,
enabling querying of the available outputs for specific tag matches.
E.g.
```python

from hamilton import driver
dr = driver.Driver(...)  # create driver as required
all_possible_outputs = dr.list_available_variables()
desired_outputs = [o.name for o in all_possible_outputs
                   if 'my_tag_value' == o.tags.get('my_tag_key')]
output = dr.execute(desired_outputs)
```

## @check_output

The `@check_output` decorator enables you to add simple data quality checks to your code.

For example:

```python
import pandas as pd
import numpy as np
from hamilton.function_modifiers import check_output

@check_output(
    data_type=np.int64,
    data_in_range=(0,100),
)
def some_int_data_between_0_and_100() -> pd.Series:
    pass
```

The check_output validator takes in arguments that each correspond to one of the default validators.
These arguments tell it to add the default validator to the list. The above thus creates
two validators, one that checks the datatype of the series, and one that checks whether the data is in a certain range.


Note that you can also specify custom decorators using the `@check_output_custom` decorator.
`check_output` and `check_output_custom` accept the `_target` parameter, which specifies *which* output to check.

See [data_quality](data_quality.md) for more information on available validators and how to build custom ones.

## @subdag

The `@subdag` decorator enables you to rerun components of your DAG with varying parameters. Note that this is immensely powerful -- if we
draw analogies from Apache Hamilton to standard procedural programming paradigms, we might have the following correspondence:

- `config.when` + friends -- `if/else` statements
- `parameterize`/`extract_columns` -- `for` loop
- `does` -- effectively macros
And so on. `subdag` takes this one step further.
- `subdag` -- subroutine definition
E.G. take a certain set of nodes, and run them with specified parameters.

Why might you want to use this? Let's take a look at some examples:

1. You have a feature engineering pipeline that you want to run on multiple datasets. If its exactly the same, this is perfect. If not, this
works perfectly as well, you just have to utilize different functions in each or the `config.when` + `config` parameter to rerun it.
2. You want to train multiple models in the same DAG that share some logic (in features or training) -- this allows you to reuse and continually add more.
3. You want to combine multiple similar DAGs (e.g. one for each business line) into one so you can build a cross-business line model.

This basically bridges the gap between the flexibility of non-declarative pipelining frameworks with the readability/maintainability of declarative ones.

Let's take a look at a simplified example (in [examples/](examples/reusing_functions/reusable_subdags.py)).

```python
@extract_columns("timestamp", "user_id", "region")  # one of "US", "CA" (canada)
def website_interactions() -> pd.DataFrame:
    return ...

def interactions_filtered(website_interactions: pd.DataFrame, region: str) -> pd.DataFrame:
    """Filters interactions by region -- note this will be run differently depending on the region its in"""
    pass

def unique_users(filtered_interactions: pd.DataFrame, grain: str) -> pd.Series:
    """Gives the number of shares traded by the frequency"""
    return ...

@subdag(
    unique_users, interactions_filtered,
    inputs={"grain": value("day")},
    config={"region": "US"},
)
def daily_users_US(unique_users: pd.Series) -> pd.Series:
    """Calculates quarterly data for just US users
    Note that this just returns the output. You can modify it if you'd like!
    """

    return unique_users


@subdag(
    unique_users, interactions_filtered,
    inputs={"grain": value("day")},
    config={"region": "CA"},
)
def daily_users_CA(unique_users: pd.Series) -> pd.Series:
    """Calculates quarterly data for just Canada users"""
    return unique_users
```

This example tracks users on a per-value user data. Specifically, we track the following:

1. Daily user data for Canada
2. Quarterly user data for the US

These each live under a separate namespace -- this exists solely so the two sets of similar nodes can coexist.
Note this set is contrived to demonstrate functionality -- it should be easy to imagine how we could add more variations.

The inputs to the `subdag` decorator takes in a variety of inputs that determine _which_ possible set of functions will constitute the DAG, and then specifically _what_ the DAG is and _how_ it is connected.
- _which_ functions constitute the subdag is specified by the `*args` input, which is a collection of modules/functions. These are used to determine the functions (i.e. nodes) that could end up in the produced subDAG.
- _what_ the sub-DAG is, and _how_ it is connected is specified by two parameters. `config` provides configuration to use to generate the subDAG (in this case the region), and `inputs` provides inputs to connect the subdag with the current DAG (similar in spirit to `@parameterize`).


Note that, if you wanted to do this functionality without this decorator, you'd have two options:
1. Rewrite every function for each scenario -- this is repetetive and doesn't scale
2. Utilize the `driver` within the functions -- E.G.

```python
def daily_users_CA(unique_users: pd.Series) -> pd.Series:
    """Calculates quarterly data for just canada users"""
    dr = hamilton.driver.Driver({"region" : "CA"}, unique_users, interactions_filtered)
    return dr.execute(["unique_users"], inputs={"grain": value("day")})["unique_users"]
```

While this is a clever approach (and you can use it if you want), there are a few drawbacks:

1. You have no visibility into the subdag -- hamilton has no knowledge about what's being run
2. Any execution parameters have to be reproduced for the driver. E.G. running on dask, etc..., is unknown to the driver.
3. DAG compilation is done at runtime -- you would not know any type-errors until the function is running

That said, this *is* a good mental model for explaining subdag functionality. Think about
it as a driver within a function, but in a way that hamilton can understand and operate.
Best of both worlds!

## @parameterize_extract_columns

`@parameterize_extract_columns` gives you the power of both `@extract_columns` and `@parameterize` in one decorator.

It takes in a list of `Parameterized_Extract` objects, each of which is composed of:
1. A list of columns to extract, and
2. A parameterization that gets used

In the following case, we produce four columns, two for each parameterization.

```python
import pandas as pd
from function_modifiers import parameterize_extract_columns, ParameterizedExtract, source, value
@parameterize_extract_columns(
    ParameterizedExtract(
        ("outseries1a", "outseries2a"),
        {"input1": source("inseries1a"), "input2": source("inseries1b"), "input3": value(10)},
    ),
    ParameterizedExtract(
        ("outseries1b", "outseries2b"),
        {"input1": source("inseries2a"), "input2": source("inseries2b"), "input3": value(100)},
    ),
)
def fn(input1: pd.Series, input2: pd.Series, input3: float) -> pd.DataFrame:
    return pd.concat([input1 * input2 * input3, input1 + input2 + input3], axis=1)
```

## @parameterize_frame

`@parameterize_frame` enables you to run parameterize_extract_columns with a dataframe specifying the parameterizations
-- allowing for less verbose specification. The above example can be rewritten as:

```python
from hamilton.experimental.decorators.parameterize_frame import parameterize_frame
df = pd.DataFrame(
        [
            ["outseries1a", "outseries2a", "inseries1a", "inseries2a", 10],
            ["outseries1b", "outseries2b", "inseries1b", "inseries2b", 100],
            # ...
        ],
        # Have to switch as indices have to be unique
        columns=[
            [
                "output1",
                "output2",
                "input1",
                "input2",
                "input3",
            ],  # configure whether column is source or value and also whether it's input ("source", "value") or output ("out")
            ["out", "out", "source", "source", "value"],
        ],
    )

@parameterize_frame(df)
def my_func(input1: pd.Series, input2: pd.Series, input3: float) -> pd.DataFrame:
    return pd.DataFrame(
        [input1 * input2 * input3, input1 + input2 + input3]
    )
```

Note that we have a double-index. Note that this is still in experimental,
and has the possibility of being changed; we'd love feedback on this
API if you end up using it!


## @model
`@model` allows you to abstract a function that is a model. You will need to implement models that make sense for
your business case. Reach out if you need examples.

Under the hood, they're just DAG nodes whose inputs are determined by a configuration parameter. A model takes in
two required parameters:
1. The class it uses to run the model. If external to Stitch Fix you will need to write your own, else internally
   see the internal docs for this. Basically the class defined determines what the function actually does.
2. The configuration key that determines how the model functions. This is just the name of a configuration parameter
   that stores the way the model is run.

The following is an example usage of `@model`:

```python
import pandas as pd
from hamilton.function_modifiers import model
import internal_package_with_logic

@model(internal_package_with_logic.GLM, 'model_p_cancel_manual_res')
# This runs a GLM (Generalized Linear Model)
# The associated configuration parameter is 'model_p_cancel_manual_res',
# which points to the results of loading the model_p_cancel_manual_res table
def prob_cancel_manual_res() -> pd.Series:
    pass
```

`GLM` here is not part of the hamilton framework, and instead a user defined model.

Models (optionally) accept a `output_column` parameter -- this is specifically if the name of the function differs
from the output column that it should represent. E.G. if you use the model result as an intermediate object, and manipulate
it all later. At Stitch Fix this is necessary because various dependent columns that a model queries
(e.g. `MULTIPLIER_...` and `OFFSET_...`) are derived from the model's name.

## A mental model for decorators

Decorators fall under a few broad categories:

1. Decorators that decide whether a function should resolves into a node (E.G. config.when())
2. Decorators that *turn* a function into a set of nodes (E.G. `@does`)
3. Decorators that modify a set of nodes, turning it into another set of nodes (E.G. `@parameterize`, `@extract_columns`, and `@check_output`)

Note the distinction between "functions" and "nodes". "functions" are what the user writes, and in the plain case,
correspond 1:1 to nodes. Nodes are then generated from functions -- decorators control how that happens. Thus, one
function can correspond to 0, 1 or many nodes.

The decorators that do this are broken up into subclasses that each have various nuances, one of which is whether or not they allow layering.
To layer effectively, we need to know *which* nodes a decorator will modify from the result of another decorator. For the ones
that allow this type of layers, they take in a `target_` parameter (with `_` due to the fact that they often have **kwargs) that tells *which*
nodes they should modify.

There are 4 options for `target_`:

1. None -- this is the default behavior. This only applies to nodes generated by the function that are not
depended on by any other nodes generated by the function.
2. `...` (the literal python Ellipsis). This means that *all* nodes generated by the function and its decorators
   will have the transformation applied to them.
3. A string. This means that only the node with the specified name will have the transformation applied.
4. A list of strings. This means that all nodes with the specified name will have the transformation applied.

This is very powerful, and we will likely be applying it to more decorators. Currently `tag` and `check_output` are the only
decorators that accept this parameter.

To dive into this, let's take a look at the `tag` decorator with the default `target_`:

This will only decorate `col1`, `col2`, and `col3`:

```python
import pandas as pd
from hamilton.function_modifiers import tag, extract_columns

@tag(type="dataframe")
@extract_columns("col1", "col2", "col3")
def dataframe() -> pd.DataFrame:
    pass
```

Once we decorate it with `target_="original_dataframe"`, we are now *just* decorating
the dataframe that gets extracted from (that is a node after all).

```python
import pandas as pd
from hamilton.function_modifiers import tag, extract_columns

@tag(type="dataframe", target_='original_dataframe')
@extract_columns("col1", "col2", "col3")
def dataframe() -> pd.DataFrame:
    pass
```

Whereas the following would tag all the columns we extract:

```python
import pandas as pd
from hamilton.function_modifiers import tag, extract_columns

@tag(type="extracted_column", target_=["col1", "col2", "col3"])
@extract_columns("col1", "col2", "col3")
def dataframe() -> pd.DataFrame:
    pass
```

The following would tag *everything*

```python
import pandas as pd
from hamilton.function_modifiers import tag, extract_columns

@tag(type="any_node_created", target_=...)
@extract_columns("col1", "col2", "col3")
def dataframe() -> pd.DataFrame:
    pass
```

Passing `None` to `target_` is the same as not passing it at all -- this decorates the "final" nodes as we saw in the first example.
