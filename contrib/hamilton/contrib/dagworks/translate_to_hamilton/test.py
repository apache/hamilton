# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# import __init__ as translate_to_hamilton
import __init__ as translate_to_hamilton

print(dir(translate_to_hamilton))


def test_code_segments():
    response = '''To translate this simple procedural code into Hamilton, you would define a single function representing the operation of adding `b` and `c` to produce `a`. Here's how it might look:

In `functions.py`, define the function:

```python
def a(b: float, c: float) -> float:
    """Adds b and c to get a."""
    return b + c
```

Then in `run.py`, you'd set up the Hamilton driver and execute the data flow:

```python
from hamilton import driver
import functions

dr = driver.Driver(config={}, module=functions)
result = dr.execute(["a"], inputs={"b": 1, "c": 2})  # assuming you're providing b=1, c=2 as inputs
print(result['a'])  # This will print 3, the result of addition
```

This Hamilton setup assumes that `b` and `c` are provided to the framework as inputs. If `b` and `c` were to be computed by other functions within the Hamilton framework or came from some form of data loading functions, those functions would need to be defined in `functions.py` as well, with appropriate signatures.
'''
    expected = [
        "def a(b: float, c: float) -> float:\n"
        '    """Adds b and c to get a."""\n'
        "    return b + c\n",
        "from hamilton import driver\n"
        "import functions\n"
        "\n"
        "dr = driver.Driver(config={}, module=functions)\n"
        'result = dr.execute(["a"], inputs={"b": 1, "c": 2})  # assuming you\'re '
        "providing b=1, c=2 as inputs\n"
        "print(result['a'])  # This will print 3, the result of addition\n",
    ]
    actual = translate_to_hamilton.code_segments(response)
    assert actual == expected
