-- Licensed to the Apache Software Foundation (ASF) under one
-- or more contributor license agreements.  See the NOTICE file
-- distributed with this work for additional information
-- regarding copyright ownership.  The ASF licenses this file
-- to you under the Apache License, Version 2.0 (the
-- "License"); you may not use this file except in compliance
-- with the License.  You may obtain a copy of the License at
--
--   http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing,
-- software distributed under the License is distributed on an
-- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
-- KIND, either express or implied.  See the License for the
-- specific language governing permissions and limitations
-- under the License.


/*
  Basic DBT model to load data from the duckdb table
*/

{{ config(materialized='table') }}

SELECT
    tbl_passengers.pid,
    tbl_passengers.pclass,
    tbl_passengers.sex,
    tbl_passengers.age,
    tbl_passengers.parch,
    tbl_passengers.sibsp,
    tbl_passengers.fare,
    tbl_passengers.embarked,
    tbl_passengers.name,
    tbl_passengers.ticket,
    tbl_passengers.boat,
    tbl_passengers.body,
    tbl_passengers."home.dest",
    tbl_passengers.cabin,
    tbl_targets.is_survived as survived
FROM
    tbl_passengers
JOIN
    tbl_targets
ON
    tbl_passengers.pid=tbl_targets.pid
