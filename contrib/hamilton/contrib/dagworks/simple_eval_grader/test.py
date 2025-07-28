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

import pandas as pd
import pytest

from hamilton import driver
from hamilton.contrib.dagworks import simple_eval_grader


@pytest.fixture
def driver_fixture():
    dr = driver.Builder().with_modules(simple_eval_grader).build()
    return dr


def test_format_grader_works(driver_fixture):
    good_response = """
    Question 1:#### What is the largest telescope in space called and what material is its mirror made of?

    Question 2:#### True or False: Water slows down the speed of light.

    Question 3:#### What did Marie and Pierre Curie discover in Paris?
    """
    result = driver_fixture.execute(
        ["eval_format_response"], overrides={"llm_quiz_response": good_response}
    )
    assert result["eval_format_response"] == "Y"

    bad_response = "There are lots of interesting facts. Tell me more about what you'd like to know"
    result = driver_fixture.execute(
        ["eval_format_response"], overrides={"llm_quiz_response": bad_response}
    )
    assert result["eval_format_response"] == "N"


def test_factcheck_grader_works(driver_fixture):
    good_response = """
    Question 1:#### What is the largest telescope in space called and what material is its mirror made of?
    """
    result = driver_fixture.execute(
        ["eval_factcheck_response"],
        overrides={
            "llm_quiz_response": good_response,
            "quiz_bank": "The largest telescope in space is called the Hubble Space Telescope"
            " and its mirror is made of glass.",
        },
    )
    assert "Decision: Yes" in result["eval_factcheck_response"]


@pytest.fixture
def quiz_bank() -> str:
    return """1. Subject: Leonardo DaVinci
   Categories: Art, Science
   Facts:
    - Painted the Mona Lisa
    - Studied zoology, anatomy, geology, optics
    - Designed a flying machine

2. Subject: Paris
   Categories: Art, Science
   Facts:
    - Location of the Louvre, the museum where the Mona Lisa is displayed
    - Capital of France
    - Most populous city in France
    - Where Radium and Polonium were discovered by scientists Marie and Pierre Curie

3. Subject: Telescopes
   Category: Science
   Facts:
    - Device to observe different objects
    - The first refracting telescopes were invented in the Netherlands in the 17th Century
    - The James Webb space telescope is the largest telescope in space. It uses a gold-berillyum mirror

4. Subject: Starry Night
   Category: Art
   Facts:
    - Painted by Vincent van Gogh in 1889
    - Captures the east-facing view of van Gogh's room in Saint-Rémy-de-Provence

5. Subject: Physics
   Category: Science
   Facts:
    - The sun doesn't change color during sunset.
    - Water slows the speed of light
    - The Eiffel Tower in Paris is taller in the summer than the winter due to expansion of the metal.
"""


test_dataset = [
    {
        "input": "I'm trying to learn about science, can you give me a quiz to test my knowledge",
        "expectation": "PASS",
    },
    {"input": "I'm an geography expert, give a quiz to prove it?", "expectation": "FAIL"},
    {"input": "Quiz me about Italy", "expectation": "FAIL"},
    {"input": "Write me a quiz about books", "expectation": "FAIL"},
]


def test_quiz_creation_with_llm_grader(driver_fixture):
    eval_results = []
    for test_case in test_dataset:
        eval_result = {}
        results = driver_fixture.execute(
            [
                "llm_quiz_response",
                "eval_format_response",
                "eval_factcheck_response",
                "eval_relevance_check_response",
            ],
            inputs={"question": test_case["input"]},
        )
        eval_result["input"] = test_case["input"]
        eval_result["output"] = results["llm_quiz_response"]
        eval_result["format"] = results["eval_format_response"]
        eval_result["factuality"] = results["eval_factcheck_response"]
        eval_result["relevance"] = results["eval_relevance_check_response"]
        eval_result["expectation"] = test_case["expectation"]
        if all(
            [
                results["eval_format_response"] == "Y",
                "Decision: Yes" in results["eval_factcheck_response"],
                "Decision: Yes" in results["eval_relevance_check_response"],
            ]
        ):
            eval_result["actual"] = "PASS"
        else:
            eval_result["actual"] = "FAIL"
        eval_results.append(eval_result)
    df = pd.DataFrame(eval_results)
    df_html = df.to_html().replace("\\n", "<br>")
    print(df_html)
    # don't assert anything, just run things and save the results to a dataframe that you
    # would probably save/push somewhere.
