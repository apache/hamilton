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

import analysis

from hamilton import base, driver
from hamilton.io.materialization import to
from hamilton.plugins import h_experiments, matplotlib_extensions, pandas_extensions  # noqa: F401


def main():
    config = dict(
        model="boosting",
        preprocess="none",
    )

    tracker_hook = h_experiments.ExperimentTracker(
        experiment_name="forecast",
        base_directory="./experiments",
    )

    dr = (
        driver.Builder()
        .with_modules(analysis)
        .with_config(config)
        .with_adapters(tracker_hook)
        .build()
    )

    inputs = dict(n_splits=3)

    materializers = [
        to.pickle(
            id="trained_model_pickle",
            dependencies=["trained_model"],
            path="./trained_model.pickle",
        ),
        to.parquet(
            id="prediction_df_parquet",
            dependencies=["prediction_df"],
            path="./prediction_df.parquet",
        ),
        to.json(
            id="cv_scores_json",
            dependencies=["cv_scores"],
            combine=base.DictResult(),
            path="./cv_scores.json",
        ),
        to.plt(
            id="prediction_plot__png",
            dependencies=["prediction_plot"],
            path="./prediction_plot.png",
        ),
    ]

    dr.visualize_materialization(
        *materializers,
        inputs=inputs,
        output_file_path=f"{tracker_hook.run_directory}/dag",
        render_kwargs=dict(view=False, format="png"),
    )

    dr.materialize(*materializers, inputs=inputs)


if __name__ == "__main__":
    main()
