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

# Modeling Pregnancy Due Dates using Apache Hamilton

This is an example of developing and applying a simple statistical model using Apache Hamilton
for a very common problem. What is the probability that a baby will be born (before, on, after)
X date?


You can find the notebook on google collab here:
<a target="_blank" href="https://colab.research.google.com/github/DAGWorks-Inc/hamilton/blob/main/examples/due_date_probabilities/notebook.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open Me In Google Colab"/>
</a>

You can read the full description in the [post](https://blog.dagworks.io/p/181bb751-2e58-4e76-8d53-5a8c81ea16cb).

In this, you'll find the following files:

1. [notebook.ipynb](notebook.ipynb) - The Jupyter notebook that walks through the process of developing/running the model.
2. [base_dates.py] -- a Apache Hamilton module that generates date-related series
3. [probability_estimation.py] -- a Apache Hamilton module that computes a statistical model (estimating parameters for probability due dates)
4. [probabilities.py] -- a Apache Hamilton module that runs that model over a set of dates

Run the notebook to see the process of developing the model and running it.
