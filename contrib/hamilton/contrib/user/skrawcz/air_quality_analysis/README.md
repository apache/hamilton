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

# Purpose of this module

This code is based on the example presented in
https://github.com/numpy/numpy-tutorials/blob/main/content/tutorial-air-quality-analysis.md

What we've done here is made a dataflow of the computation required to do an AQI analysis.
It's very easy to change these functions for more sophisticated analysis, as well as to
change the inputs, etc.

Note: this code here is really to show you how to use pure numpy, not the best practices way of doing analysis.
In real-life practice you would probably do the following:
* The pandas library is preferable to use for time-series data analysis.
* The SciPy stats module provides the stats.ttest_rel function which can be used to get the t statistic and p value.
* In real life, data is generally not normally distributed. There are tests for such non-normal data like the
  Wilcoxon test.

You can download some data to use [here](https://raw.githubusercontent.com/apache/hamilton/main/examples/numpy/air-quality-analysis/air-quality-data.csv),
or download the following way:
```bash
wget https://raw.githubusercontent.com/apache/hamilton/main/examples/numpy/air-quality-analysis/air-quality-data.csv
```

# Configuration Options
There is no configuration required for this dataflow. So pass in an empty dictionary.

# Limitations

None to really note.
