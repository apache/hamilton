<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Apache Hamilton notebook extension

One of the best part about notebooks is the ability to execute and immediately inspect results. They provide a "read-eval-print" loop (REPL) coding experience. However, the way Apache Hamilton separates dataflow definition (functions in a module) from execution (building and executing a driver) creates an extra step that can slowdown this loop.

We built the Apache Hamilton notebook extension to tighten that loop and even give a better experience than the core notebook experience!

For a [video overview click here](https://www.youtube.com/watch?v=Z3ZT2ur2jg8&t=288s).

To load the magic:
```python
%load_ext hamilton.plugins.jupyter_magic
```

For example, this would allow you to define the module `joke` from your notebook

```python
%%cell_to_module joke --display
def topic() -> str:
    return "Cowsay"

def joke_prompt(topic: str) -> str:
    return f"Knock, knock. Who's there? {topic}"

def reply(joke_prompt: str) -> str:
    _, _, right = joke_prompt.partition("? ")
    return f"{right} who?"
```

Go explore `example.ipynb` to learn about all interactive features!

To exercise this example you can run it in Google Colab too:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/jupyter_notebook_magic/example.ipynb)
