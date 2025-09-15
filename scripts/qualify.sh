#!/bin/zsh
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

cd examples
pushd hello_world
pwd
echo "-----hello world----"
python my_script.py
popd
pushd numpy/air-quality-analysis
pwd
echo "-----Numpy----"
python run_analysis.py
popd
pushd model_examples/scikit-learn
pwd
echo "---- ML example ---"
python run.py iris svm
popd
pushd ray/hello_world
pwd
echo "-----ray-------"
python run.py
echo "----- ray workflow -----"
python run_rayworkflow.py
popd
pushd dask/hello_world
pwd
echo "---- dask 1 ----"
python run.py
echo "----- dask with delayed ----"
python run_with_delayed.py
echo "---- dask delayed with objects ----"
python run_with_delayed_and_dask_objects.py
popd
pushd data_quality/simple/
echo "---- data quality simple----"
python run.py
echo "--- data quality ray ----"
python run_ray.py
echo "----- data quality dask ----"
python run_dask.py
popd
pushd data_quality/pandera/
echo "---- pandera simple ---"
python run.py
echo "---- pandera ray ---"
python run_ray.py
echo "---- pandera dask ---"
python run_dask.py
popd
pushd lineage
echo "---- lineage script ----"
python lineage_script.py
python lineage_commands.py PII
python lineage_commands.py visualize upstream training_set_v1 tsv1
python lineage_commands.py path age fit_random_forest
popd
pushd spark/pandas_on_spark
echo "---- pandas on spark ----"
python run.py
popd
pushd pandas/materialization
echo "---- pandas materializers ----"
python my_script.py
rm -rf df.*  # removes files created.
popd
echo "---- parallel examples -----"
pushd parallelism/file_processing
python run.py --mode dask
python run.py --mode ray
python run.py --mode multithreading
python run.py --mode local
popd
echo "----- styling viz -----"
pushd styling_visualization
python run.py
popd
echo "---- ibis -------"
pushd ibis/feature_engineering
python run.py --level column # --model linear
popd
echo "---- scraping ----"
pushd LLM_Workflows/scraping_and_chunking
python run.py > scraping.out
popd
echo "---- experiment tracker ----"
pushd experiment_management
python run.py
popd
echo "---- polars test cases ----"
pushd polars
python my_script.py
pushd lazyframe
python my_script.py
popd
popd
echo "---- schema test cases ---"
pushd schema
python dataflow.py
popd
echo "----- ui SDK test cases -- you need to have the UI running ---"
pushd hamilton_ui
python run.py --username elijah@dagworks.io --project-id=1
popd
echo "----- Ray Tracker + SDK test cases -- you need to have the UI running ---"
pushd ray/ray_Hamilton_UI_tracking
python run.py
popd
