# Purpose of this module

This module is used to customize embeddings for text data. It is based on MIT licensed code from
this [OpenAI cookbook](https://github.com/openai/openai-cookbook/blob/main/examples/Customizing_embeddings.ipynb).

The output is a matrix that you can use to multiply your embeddings. The product of this multiplication is a
'custom embedding' that will better emphasize aspects of the text relevant to your use case.
In binary classification use cases, the OpenAI cook book author claims to have seen error rates drop by as much as 50%.

Why customize embeddings? Embeddings are a way to represent text as a vector of numbers. The numbers are chosen so that
similar words have similar vectors. For example, the vectors for "cat" and "dog" will be closer together than the
vectors for "cat" and "banana". Embeddings are useful for many NLP tasks, such as sentiment analysis, text classification,
and question answering. Embeddings are often trained on a large corpus of text, such as Wikipedia. However, these
embeddings may not be optimal for a specific task. E.g. you may want to be able to distinguish between "cat" and "dog"
for a specific task, but the embeddings may not allow you to do that reliably. This module allows you to customize some
embeddings for a specific task, e.g. by making the vectors for "cat" and "dog" further apart.

## How might I use this module?
If you pass in `{"source":"snli"}` as configuration to the driver, the module will download the corpus and unzip it and
use that as input to optimize embeddings for. The embeddings of sentences are optimized for the task of predicting
whether a sentence pair is "entailment", or "contradiction". That is, each pair of sentences are logically entailed
(i.e., one implies the other). These pairs are our positives (label = 1). We generate synthetic negatives by combining
sentences from different pairs, which are presumed to not be logically entailed (label = -1).

If you pass in `{"source":"local"}` as configuration to the driver, the module will load a local dataset you provide a
path to. The dataset should be a csv with columns "text_1", "text_2", and "label". The label should be +1 if the text
pairs are similar and -1 if the text pairs are dissimilar.

Otherwise if you pass in `{}` as configuration to the driver, the module will require you to pass in a dataframe as
`processed_local_dataset` as an input. The dataframe should have columns "text_1", "text_2", and "label". The label should be +1 if the
text pairs are similar and -1 if the text pairs are dissimilar.

In general to use this module you'll need to do the following:

1. Create a dataset of text pairs, where each pair is either similar or dissimilar. Mechanically that means you'll need
to modify/override `processed_local_dataset()` so that you output a dataset of [text_1, text_2, label] where label is +1 if
the pairs of text are similar and -1 if the pairs of text are dissimilar. See the docstring for `processed_local_dataset()`.
2. Modify the "hyperparameters" for a couple of the functions, e.g. `optimize_matrix()`, to suit your needs.
3. Modify how embeddings are generated, e.g. `_get_embedding()`, to suit your needs.
4. Adjust any logic for creating negative pairs, that is, modify `_generate_negative_pairs()`, to suit your needs. For
example, if you have multi-class labels you'll have to modify how you generate negative pairs.
5. Profit!

To execute the DAG, the recommended outputs to grab are:

```python
outputs=[
    "train_accuracy",
    "test_accuracy",
    "embedded_dataset_histogram",
    "test_accuracy_post_optimization",
    "accuracy_plot",
    "training_and_test_loss_plot",
    "customized_embeddings_dataframe",
    "customized_dataset_histogram",
]
```

You should be able to read the module top to bottom which corresponds roughly to the order of execution.

## What type of functionality is in this module?
The module includes functions for getting embeddings, calculating cosine similarity, processing datasets, splitting data,
generating negative pairs, optimizing matrices, and plotting results. It also shows how one can use `@config.when`
to swap out how the data is loaded, `@check_output` for schema validation of a dataframe, `@parameterize` for
creating many functions from a single function, and `@inject` to collect results from the results of `@parameterize`.

The module uses libraries such as numpy, pandas, plotly, torch, sklearn, and openai.

# Configuration Options
`{"source": "snli"}` will use the Stanford SNLI corpus. Use this to run the code as-is.

`{"source": "local"}` will load a local dataset you provide a path to.

`{}` will require you to pass in a dataframe with name `raw_data` as an input.

# Limitations
This code is currently set up to work with OpenAI. It could be modified to work with other embedding producers/providers.

The matrix optimization is not set up to be parallelized, though it could be done using Apache Hamilton constructs,
like `Parallelizeable`.
