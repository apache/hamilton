# Purpose of this module

The purpose of this module is to provide you with a dataflow to translate
your existing procedural code into code written in the Apache Hamilton style.

```python
# Make sure you have an API key in your environment, e.g. os.environ["OPENAI_API_KEY"]
# import translate_to_hamilton via the means that you want. See above code.

from hamilton import driver

dr = (
    driver.Builder()
        .with_config({})
        .with_modules(translate_to_hamilton)
        .build()
)

user_code = "a = b + c"  # replace with your code here
result = dr.execute(
    ["code_segments", "translated_code_response"], # request these as outputs
    inputs={"user_code": user_code, "model_name": "gpt-4-1106-preview"}
)
print(result["code_segments"])
```
For a jupyter notebook example, see [this link](https://github.com/apache/hamilton/tree/main/examples/contrib/notebooks/dagworks-translate_to_hamilton).

## What you should modify

The prompt used here is fairly generic. If you are going to be doing larger scale refactoring
of code, you should modify the prompt to be more specific to your use case.

If you're going to use a different model than `gpt-4-1106-preview`, you will likely need to modify the prompt.

# Configuration Options
There is no configuration required for this module.

# Limitations

The current prompt was designed for the `gpt-4-1106-preview` model. If you are using a different model,
you will likely need to modify the prompt. Otherwise, we're still tweaking the prompts. We expect to add to
the prompt based on the model you're using underneath. Please reach out and give use feedback.

This module uses litellm to enable you to easily change the underlying model provider.
See https://docs.litellm.ai/ for documentation on the models supported.

You need to include the respective LLM provider's API_KEY in your environment.
e.g. OPENAI_API_KEY for openai, COHERE_API_KEY for cohere, etc. and should be
accessible from your code by doing `os.environ["OPENAI_API_KEY"]`, `os.environ["COHERE_API_KEY"]`, etc.

The code does not check the context length, so it may fail if the context passed is too long. If that's
the case, translate smaller chunks of code with `without_driver=True` as an input.
