# Purpose of this module
This module shows you how to fine-tune an LLM model. This code is inspired by this [fine-tuning code](https://github.com/dagster-io/dagster_llm_finetune/tree/main).

Specifically the code here, shows Supervised Fine-Tuning (SFT) for dialogue. This approach instructs the model to be more
useful to directly respond to a question, rather than optimizing over an entire dialogue. SFT is the most common type of fine-tuning,
as the other two options, Pre-training for Completion, and RLHF, required more to work. Pre-training requires more computational power,
while RLHF requires higher-quality dialogue data.

This code should work on a regular CPU (in a docker container), which will allow you to test out the code locally without
any additional setup. This specific approach this code uses is [LoRA](https://arxiv.org/abs/2106.09685) (low-rank adaptation of large language models), which
means that only a subset of the LLM's parameters are tweaked and prevents over-fitting.

Note: if you have issues running this on MacOS, reach out, we might be able to help.

## What is fine-tuning?
Fine-tuning is when a pre-trained model, in this context a foundational model, is customized using additional data to
adjust its responses for a specific task. This is a good way to adjust an off-the-shelf, i.e. pretrained model, to provide
more responses that are more contextually relevant to your use case.

## FLAN LLM
This example is based on using [Google's Fine-tuned LAnguage Net (FLAN) models hosted on HuggingFace](https://huggingface.co/docs/transformers/model_doc/flan-t5).
The larger the model, the longer it will take to fine-tune, and the more memory you'll need for it. The code
here was validated to run on docker using the smallest FLAN model ("model_id": "google/flan-t5-small") on a Mac that's a few years old.

## What type of functionality is in this module?

The module uses libraries such as numpy, pandas, plotly, torch, sklearn, peft, evaluate, datasets, and transformers.

It shows a basic process of:

a. Loading data and tokenizing it and setting up some tokenization parameters.

b. Splitting data into training, validation, and hold out sets.

c. Fine-tuning the model using LoRA.

d. Evaluating the fine-tuned model using the [rouge metric](https://en.wikipedia.org/wiki/ROUGE_(metric)).

You should be able to read the module top to bottom which corresponds roughly to the order of execution.

## How might I use this module?
To use this module you'll need to do the following:

- Data. The data set should be list of JSON objects, where each entry in the list is an object that has the "question" and
and also the "answer" to that question. You will provide the name of the keys for these fields as input to run the code.
e.g. you should be able to do `json.load(f)` and it would return a list of dictionaries, e.g. something like this:

```python
[
    {
        "question": "What is the meaning of life?",
        "reply": "42"
    },
    {
        "question": "What is Apache Hamilton?",
        "reply": "..."
    },
    ...
]
```

You would then pass in as _inputs_ to execution `"data_path":PATH_TO_THIS_FILE` as well as `"input_text_key":"question"` and `"output_text_key":"reply"`.
- Instantiate the driver. Use `{"start": "base"}` as configuration to run with to use a raw base LLM to finetune.
- Pick your LLM. `"model_id":"google/mt5-small"` is what we recommend to start, but you can change it to any of the models
that the transformers library supports for `AutoModelForSeq2SeqLM` models.
- Run the code.

```python
# instantiate the driver with this module however you want
result = dr.execute(
    [ # some suggested outputs -- see the visualization/code to understand what these are
        "save_best_models",
        "hold_out_set_predictions",
        "training_and_validation_set_metrics",
        "finetuned_model_on_validation_set",
    ],
    inputs={
        "model_id": "google/flan-t5-small", # the base model you want to fine-tune
        "data_path": "example-support-dataset.json", # the path to your dataset
        "input_text_key": "question",  # the key in the json object that has the input text
        "output_text_key": "gpt4_replies_target", # the key in the json object that has the target output text
    },
)
```

### Running the code in a docker container
The easiest way to run this code is to use a docker container, unless you have experience with
GPUs. After writing a module that uses the code here, e.g. `YOUR_RUN_FILE.py`, you can create a dockerfile
that looks like this to then execute your fine-tuning code. Note, replace `example-support-dataset.json` with
your dataset that you want to fine-tune on.

```docker
FROM python:3.10-slim-bullseye

WORKDIR /app

# install graphviz backend
RUN apt-get update \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# change this to your data set if you want to load
# it into the container
COPY example-support-dataset.json .

COPY . .

EXPOSE 8080:8080

# run the code that you wrote that invokes this module
CMD python YOUR_RUN_FILE.py
```
Then to run this it's just:
```bash
docker build -t YOUR_IMAGE_NAME .
docker run YOUR_IMAGE_NAME
```

# Configuration Options
 - `{"start": "base"}` Suggested configuration to run with to use a raw base LLM to finetune.
 - `{"start":  "presaved"}` Use this if you want to load an already fine-tuned model and then just eval it.

# Limitations
The code here will likely not solve all your LLM troubles,
but it can show you how to fine-tune an LLM using parameter-efficient techniques such as LoRA.

This code is currently set up to work with dataset and transformer libraries. It could be modified to work with other libraries.

The code here is all in a single module, it could be split out to be more modular, e.g. data loading vs tokenization vs
finetuning vs evaluation.
