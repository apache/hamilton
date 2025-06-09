# Overview

This code accompanies the ["Write once, run everywhere" blog post](https://blog.dagworks.io/p/feature-engineering-with-hamilton).
While it represents the
same fundamental concepts as the other feature engineering example, it's simplified to demonstrate a few contexts.
You should be able to download this and easily adapt it to your own use-cases.

Note: we've since added the bytewax streaming example, but that's not covered in the blog post.

# Structure

There are three scripts in this example
1. [online.py](contexts/online.py) -- meant to simulate an online server.
2. [batch.py](contexts/batch.py) -- meant to simulate a batch ETL.
3. [streaming.py](contexts/streaming.py) -- meant to simulate a streaming context.

Then we have the individual code in components.py, separated into:
1. [features.py](components/features.py) -- runs the map operations to generate the final features
2. [joins.py](components/join_operations.py) -- runs the join operations on the way to generating the features
3. [aggregations.py](components/aggregation_operations.py) -- runs the aggregation operations on the way to generating the features
4. [data_loaders.py](components/data_loaders.py) -- loads up data externally
5. [model.py](components/model.py) -- runs the model on the features

As well as a [utility file](components/utils.py) that contains some helper functions. These are mock functions to load the data.

We have chosen to place the batch/online code in the same module to make comparing easier to compare/show how one could use -- there is online/batch code in all three of these.
That said, the alternative (separating out by modules) could make sense as well.

# Running the code

Run the online.py file with:

```bash
python -m contexts.online
Usage: python -m contexts.online [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  serve      This command will start the server
  visualize  This command will visualize execution
```

And run the batch.py file with:

```bash
python -m contexts.batch
Usage: python -m contexts.batch [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  run        This command will run the ETL, and print it out to the terminal
  visualize  This command will visualize execution
```

And run the streaming.py file with:

```bash
python -m bytewax.run contexts.streaming:flow
Usage: python -m bytewax.run MODULE_WITH_FLOW
```

# Adapting to your use-case

As you've noticed, rather than implementing a model/data loading functionality (this varies by use-case),
we have exposed mock functions. To adapt this to your (real-world) use-case, you'll want to:


1. Change the functions in [utils.py](components/utils.py) to load your data, *or* make [data_loaders.py](components/data_loaders.py) and utilize the `load_from`.
2. Change to use your features by modifying, adding, and removing functions.
3. Use an actual model! Change [model.py](components/model.py) to load your pretrained model, or make it do something interesting with the input data.
4. See the commit history on this example, and see what was changed to accommodate the streaming context. You'll want to do something similar.


# Pictures of the Apache Hamilton DAG
## Batch
![batch](batch.png)
## Online
![online](online.png)
## Streaming
![streaming](streaming.png)
