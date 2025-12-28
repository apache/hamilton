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

"""
Hamilton pipeline to load fighter data into FalkorDB.
"""

import falkordb
import pandas as pd
import utils

from hamilton.htypes import Collect, Parallelizable


def raw_fighter_details() -> pd.DataFrame:
    """Load fighter data"""
    _df = pd.read_csv("../data/raw_fighter_details.csv")
    return _df


def fighter(raw_fighter_details: pd.DataFrame) -> Parallelizable[pd.Series]:
    """We then want to do something for each record. That's what this code sets up"""
    for _, row in raw_fighter_details.iterrows():
        yield row


def record(fighter: pd.Series) -> dict:
    """Given a single fighter record, process it into a dictionary."""
    attrs = {}
    attrs["Name"] = fighter.fighter_name

    if isinstance(fighter.Height, str) and fighter.Height != "":
        attrs["Height"] = utils.height_to_cm(fighter.Height)

    if isinstance(fighter.Weight, str) and fighter.Weight != "":
        Weight = int(fighter.Weight.replace(" lbs.", ""))
        attrs["Weight"] = Weight

    if isinstance(fighter.Reach, str) and fighter.Reach != "":
        attrs["Reach"] = utils.reach_to_cm(fighter.Reach)

    if isinstance(fighter.Stance, str) and fighter.Stance != "":
        attrs["Stance"] = fighter.Stance

    if isinstance(fighter.DOB, str) and fighter.DOB != "":
        attrs["DOB"] = utils.date_to_timestamp(fighter.DOB)

    # Significant Strikes Landed per Minute
    attrs["SLpM"] = float(fighter.SLpM)

    # Strike accuracy
    attrs["Str_Acc"] = utils.percentage_to_float(fighter.Str_Acc)

    # Significant Strikes Absorbed per Minute.
    attrs["SApM"] = float(fighter.SApM)

    # strikes defended
    attrs["Str_Def"] = utils.percentage_to_float(fighter.Str_Def)

    # Takedown average
    attrs["TD_Avg"] = float(fighter.TD_Avg)

    # Takedown accuracy
    attrs["TD_Acc"] = utils.percentage_to_float(fighter.TD_Acc)

    # Takedown defense
    attrs["TD_Def"] = utils.percentage_to_float(fighter.TD_Def)

    # Submission average
    attrs["Sub_Avg"] = float(fighter.Sub_Avg)
    return attrs


def write_to_graph(record: Collect[dict], graph: falkordb.Graph) -> int:
    """Take all records and then push to the DB"""
    records = list(record)
    # Load all fighters in one go.
    q = "UNWIND $fighters as fighter CREATE (f:Fighter) SET f = fighter"
    graph.query(q, {"fighters": records})
    return len(records)
