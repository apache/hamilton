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

This module implements forecasting using machine learning with `mlforecast` by Nixtla.

Fit and evaluate a list of models on a time series dataset. Obtain a cross-validation benchmark dataframe and prediction plots.

Your dataset needs to have columns `unique_id` to identify each series, `ds` to identify the time step, and `y` to specify the value of series `unique_id` at time `ds`.

# Configuration Options
## Config.when
This module doesn't receive configurations.

## Inputs
- `freq`: Adjust to meet the sampling rate of your time series
- `cross_validation_predictions()` and `inference_predictions()` share some arguments to provide consistency between evaluation and inference. Arguments that you might want to decouple are prefixed with `cv_` or `inference_` respectively.
- `target_transforms`: Pass a list of transforms to rescale, detrend, etc. your target and make it easier to fit and predict.
- ⚠ `num_threads`: Set the number of cores to use for compute. The default value `-1` will use all available cores and might slowdown the machine in the meantime.

## Overrides
- `base_models`: Create a list of sklearn-compatible models to fit and evaluate ([docs](https://nixtla.github.io/statsforecast/src/core/models.html))
- `lag_transforms` and `date_features`: Should be overriden to pass values relevant to your dataset
- `evaluation_metrics`: Set the list of Nixtla-compatible metrics to use during cross-validation ([examples](https://github.com/Nixtla/utilsforecast/blob/main/utilsforecast/losses.py))


# Limitations
- You should implement your the `lag_transforms()`, `date_features()`, and `target_transforms` that best suit your problem.
