# Feature Engineering in Multiple Contexts

What is feature engineering? It's the process of transforming data for input to a "model".

To make models better, it's common to perform and try a lot of "transforms". This is where Apache Hamilton comes in.
Apache Hamilton allows you to:
* write different transformations in a straightforward and formulaic manner
* keep them managed and versioned with computational lineage (if using something like git)
* has a great testing and documentation story

which allows you to sanely iterate, maintain, and determine what works best for your modeling domain.

In this series of examples, we'll skip talking about the benefits of Apache Hamilton here, and instead focus on how to use it
for feature engineering. But first, some context on what challenges you're likely to face with feature engineering
in general.

# What is hard about feature engineering?
There are certain dimensions that make feature engineering hard:

1. Code: Organizing and maintaining code for reuse/collaboration/discoverability.
2. Lineage: Keeping track of what data is being used for what purpose.
3. Deployment: Offline vs online vs streaming needs.

## Code: Organizing and maintaining code for reuse/collaboration/discoverability.
> Individuals build features, but teams own them.

Have you ever dreaded taking over someone else's code? This is a common problem with feature engineering!

Why? The code for feature engineering is often spread out across many files, and created by many individuals.
E.g. scripts, notebooks, libraries, etc., and written in many ways. This makes it hard to reuse code,
collaborate, discover what code is available, and therefore maintain what is actually being used in "production" and
what is not.

## Lineage: Keeping track of what data is being used for what purpose
With the growth of data teams, along with data governance & privacy regulations, the need for knowing and understanding what
data is being used and for what purpose is important for the business to easily answer. A "modeler" a lot of the times
is not a stakeholder in needing this visibility, they just want to build models, but these concerns are often put on
their plate to address, which slows down their ability to build and ship features and thus models.

Not having lineage or visibility into what data is being used for what purpose can lead to a lot of problems:
 - teams break data assumptions without knowing it, e.g. upstream team stops updating data used downstream.
 - teams are not aware of what data is available to them, e.g. duplication of data & effort.
 - teams have to spend time figuring out what data is being used for what purpose, e.g. to audit models.
 - teams struggle to debug inherited feature workflows, e.g. to fix bugs or add new features.


## Deployment: Offline vs online vs streaming needs
This is a big topic. We wont do it justice here, but let's try to give a brief overview of two main problems:

(1) There are a lot of different deployment needs when you get something to production. For example, you might want to:
   - run a batch job to generate features for a model
   - hit a webservice to make predictions in realtime that needs features computed on the fly, or retrieved from a cache (e.g. feature store).
   - run a streaming job to generate features for a model in realtime
   - require all three or a subset of the above ways of deploying features.

So the challenge is, how do you design your processes to take in account your deployment needs?

(2) Implement features once or twice or thrice? To enable (1), you need to ask yourself, can we share features? or
do we need to reimplement them for every system that we want to use them in?

With (1) and (2) in mind, you can see that there are a lot of different dimensions to consider when designing your
feature engineering processes. They have to connect with each other, and be flexible enough to support your specific
deployment needs.

# Using Apache Hamilton for Feature Engineering for Batch/Offline
If you fall into **only** needing to deploy features for batch jobs, then stop right there. You don't need these examples,
as they are focused on how to bridge the gap between "offline" and "online" feature engineering. You should instead
browse the other examples like `data_quality`.

# Using Apache Hamilton for Feature Engineering for Batch/Offline and Online/Streaming
These example scenarios here are for the people who have to deal with both batch and online feature engineering.

We provide two examples for two common scenarios that occur if you have this need. Note, the example code in these
scenarios tries to be illustrative about how to think and frame using Apache Hamilton. It contains minimal features so as to
not overwhelm you, and leaves out some implementation details that you would need to fill in for your specific use case,
e.g. like fitting a model using the features, or where to store aggregate feature values, etc.

## Scenario Context
A not too uncommon task is that you need to do feature engineering in an offline (e.g. batch via airflow)
setting, as well as an online setting (e.g. synchronous request via FastAPI). What commonly
happens is that the code for features is not shared, and results in two implementations
that result in subtle bugs and hard to maintain code.

With this example series, we show how you can use Apache Hamilton to:

1. write a feature once. (scenarios 1 and 2)
2. leverage that feature code anywhere that python runs. e.g. in batch and online. (scenarios 1 and 2)
3. show how to modularize components so that if you have values cached in a feature store,
you can inject those values into your feature computation needs. (scenario 2)

The task that we're modeling here isn't that important, but if you must know, we're trying to predict the number of
hours of absence that an employee will have given some information about them; this is based off the `data_quality`
example, which is based off of the [Metaflow+Apache Hamilton example](https://outerbounds.com/blog/developing-scalable-feature-engineering-dags/),
where Apache Hamilton was used for the feature engineering process -- in that example only offline feature engineering was modeled.

Assumptions we're using:
1. You have a fixed set of features that you want to compute for a model that you have determined as being useful a priori.
2. We are agnostic of the actual model -- and skip any details of that in the examples.
3. We use Pandas as the data structure in our example here because it's easy to reuse in a batch, and online context. However you
need not use Pandas if you don't want to.

Let's explain the context of the two scenarios a bit more.

## Scenario 1: the simple case - ETL + Online API
In this scenario we assume we can get the same raw inputs at prediction time, as would be provided at training time.

This is a straightforward process if all your feature transforms are [map operations](https://en.wikipedia.org/wiki/Map_(higher-order_function)).
If however you have some transforms that are aggregations, then you need to be careful about how you connect your offline
ETL with online.

In this example, there are two features, `age_mean` and `age_std_dev`, that we avoid recomputing in an online setting.
Instead, we "store" the values for them when we compute features in the offline ETL, and then use those "stored" values
at prediction time to get the right feature computation to happen.

## Scenario 2: the more complex case - request doesn't have all the raw data - ETL + Online API
In this scenario we assume we are not passed in data, but need to fetch it ourselves as part of the online API request.

We will pretend to hit a feature store, that will provide us with the required data to compute the features for
input to the model. This example shows one way to modularize your Apache Hamilton code so that you can swap out the "source"
of the data. To simplify the example, we assume that we can get all the input data we need from a feature store, rather
than it also coming in via the request. Note: if using a feature store, which is effectively a cache, you might not need
Apache Hamilton on the online side, if, and only if, you can get all the data you need from the feature store, without needing
to perform any computations. In this situation, you would push compute features to the feature store from your offline
ETL process that creates features.

A good exercise would be to make note of the differences with this scenario (2) and scenario (1) in how they structure
the code with Apache Hamilton.

# What's next?
Jump into each directory and read the README, it'll explain how the example is set up and how things should work.

# What are extensions/uses not shown here but we know you can do them
Here are two ideas that come to mind:

1. Streaming settings. Given the examples, it should be clear how to make it possbile to use Apache Hamilton in a streaming setting.
2. How to ask Apache Hamilton what features are needed as input to know what to request from the feature store. With tags, and
querying the DAG at the start of the app, you could dynamically ask Apache Hamilton what's required and then only go to the
feature store for that data. If this type of example would be of interest, let us know.
