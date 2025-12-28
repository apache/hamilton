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

import vanilla_anthropic
import vanilla_completion


def invoke_chain_with_fallback(topic: str) -> str:
    try:
        return vanilla_completion.invoke_chain(topic)
    except Exception:
        return vanilla_anthropic.invoke_anthropic_chain(topic)


if __name__ == "__main__":
    print(invoke_chain_with_fallback("ice cream"))
