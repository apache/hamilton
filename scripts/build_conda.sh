#!/bin/bash
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

CONDA_HOME=$HOME/anaconda3
# This is a script to create and build hamilton for conda.
# Be sure you have conda activated and have logged into anaconda
# conda activate && anaconda login
pkg='sf-hamilton'
# adjust the Python versions you would like to build
array=(3.10 3.11 3.12 3.13)
echo "Building conda package ..."
cd ~
# this will create a ~/sf-hamilton directory with metadata to build the package.
# will error if it already exists.
conda skeleton pypi $pkg

# building conda packages
for i in "${array[@]}"
do
	conda build --python $i $pkg
done
# convert package to other platforms
cd ~
# platforms=( linux-64 linux-32 linux-64 win-32 win-64 )
find $CONDA_HOME/conda-bld/osx-64/ -name *.tar.bz2 | while read file
do
    echo $file
    conda convert --platform all $file  -o $CONDA_HOME/conda-bld/
    #for platform in "${platforms[@]}"
    #do
    #   conda convert --platform $platform $file  -o $CONDA_HOME/conda-bld/
    #done
done
# upload packages to conda
# run `conda install anaconda-client` to install `anaconda` and do `anaconda login` (conda activate first)
find $CONDA_HOME/conda-bld/ -name "*.tar.bz2" | while read file
do
    echo $file
    anaconda upload -u Hamilton-OpenSource $file
done
echo "Built & uploaded conda package done!"
echo "To purge the build files, run: conda build purge; and then delete *.tar.bz2 files under $CONDA_HOME/conda-bld/"
