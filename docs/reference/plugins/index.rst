.. Licensed to the Apache Software Foundation (ASF) under one
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

Plugin API Reference
--------------------

Apache Hamilton includes ready-to-use adapters built on the
:doc:`Lifecycle API <../lifecycle-hooks/index>`. Some plugins require an
additional third-party library to be installed.

Add one or more adapters when building the driver:

.. code-block:: python

    dr = (
        driver.Builder()
        .with_modules(...)
        .with_adapters(
            Adapter1(...),
            Adapter2(...),
        )
        .build()
    )

.. toctree::
    PDBDebugger
    PrintLn
    ProgressBar
    RichProgressBar
    DDOGTracer
    FunctionInputOutputTypeChecker
    SlackNotifier
    GracefulErrorAdapter
    SparkInputValidator
    Narwhals
    MLFlowTracker
    NoEdgeAndInputTypeChecking
    OpenLineageAdapter
