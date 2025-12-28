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
Hamilton module to ingest fight data into FalkorDB.
"""

import falkordb
import pandas as pd
import utils

from hamilton.htypes import Collect, Parallelizable


def raw_total_fight_data() -> pd.DataFrame:
    """Loads the raw fight data"""
    _df = pd.read_csv("../data/raw_total_fight_data.csv", delimiter=";")
    return _df


def transformed_data(raw_total_fight_data: pd.DataFrame) -> pd.DataFrame:
    """Does some light transformation on the data and adds some columns"""
    _df = raw_total_fight_data
    _df.last_round = _df.last_round.astype(int)
    _df.last_round_time = _df.last_round_time.apply(lambda x: utils.time_to_seconds(x))
    _df.date = _df.date.apply(lambda x: utils.date_to_timestamp(x))
    _df["Loser"] = _df.apply(
        lambda x: x["B_fighter"] if x["Winner"] == x["R_fighter"] else x["R_fighter"], axis=1
    )
    return _df


def columns_of_interest() -> list[str]:
    """Returns the columns that we're interested in processing"""
    return [
        "R_fighter",
        "B_fighter",
        #    R_KD, B_KD, R_SIG_STR.,B_SIG_STR.,
        # R_SIG_STR_pct, B_SIG_STR_pct, R_TOTAL_STR., B_TOTAL_STR.,
        # R_TD, B_TD, R_TD_pct, B_TD_pct, R_SUB_ATT, B_SUB_ATT,
        # R_REV, B_REV, R_CTRL, B_CTRL, R_HEAD, B_HEAD, R_BODY,
        # B_BODY, R_LEG, B_LEG, R_DISTANCE, B_DISTANCE, R_CLINCH,
        # B_CLINCH, R_GROUND, B_GROUND, win_by,
        "last_round",
        "last_round_time",
        "Format",
        "Referee",
        "date",
        "location",
        "Fight_type",
        "Winner",
        "Loser",
    ]


def fight(
    transformed_data: pd.DataFrame,
    columns_of_interest: list[str],
) -> Parallelizable[pd.Series]:
    """Enables us to process each fight. We pass in a client along with each row"""
    for _idx, _row in transformed_data[columns_of_interest].iterrows():
        yield _row


def write_to_graph(fight: pd.Series, graph: falkordb.Graph) -> str:
    _row, _graph = fight, graph
    # create referee
    q = "MERGE (:Referee {Name: $name})"
    _graph.query(q, {"name": _row.Referee if isinstance(_row.Referee, str) else ""})

    # create card
    q = "MERGE (c:Card {Date: $date, Location: $location})"
    _graph.query(q, {"date": _row.date, "location": _row.location})

    # create fight
    q = """MATCH (c:Card {Date: $date, Location: $location})
           MATCH (ref:Referee {Name: $referee})
           MATCH (r:Fighter {Name:$R_fighter})
           MATCH (b:Fighter {Name:$B_fighter})
           CREATE (f:Fight)-[:PART_OF]->(c)
           SET f = $fight
           CREATE (f)-[:RED]->(r)
           CREATE (f)-[:BLUE]->(b)
           CREATE (ref)-[:REFEREED]->(f)
           RETURN ID(f)
        """
    f_id = _graph.query(
        q,
        {
            "date": _row.date,
            "location": _row.location,
            "referee": _row.Referee if isinstance(_row.Referee, str) else "",
            "R_fighter": _row.R_fighter,
            "B_fighter": _row.B_fighter,
            "fight": {
                "Last_round": _row.last_round,
                "Last_round_time": _row.last_round_time,
                "Format": _row.Format,
                "Fight_type": _row.Fight_type,
            },
        },
    ).result_set[0][0]

    # mark winner & loser
    q = """MATCH (f:Fight) WHERE ID(f) = $fight_id
           MATCH (l:Fighter {Name:$loser})
           MATCH (w:Fighter {Name:$winner})
           CREATE (w)-[:WON]->(f), (l)-[:LOST]->(f)
        """
    _graph.query(
        q,
        {
            "fight_id": f_id,
            "loser": _row.Loser,
            "winner": _row.Winner if isinstance(_row.Winner, str) else "",
        },
    )
    return "success"


def collect_writes(write_to_graph: Collect[str]) -> int:
    return len(list(write_to_graph))
