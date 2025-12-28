#!/usr/bin/env python3
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

import json
import pathlib
import sys

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build
from timewreport.parser import TimeWarriorParser

from hamilton.function_modifiers import extract_fields

DEFAULT_SHEET_ID = "Sheet1"


def timewarrior_parser() -> TimeWarriorParser:
    """Parse Timewarrior's output"""
    return TimeWarriorParser(sys.stdin)


def intervals(timewarrior_parser: TimeWarriorParser) -> list[dict]:
    """Get a list of time intervals from the parser"""
    return [
        dict(
            date=interval.get_end(),
            duration=interval.get_duration(),
            tags=interval.get_tags(),
        )
        for interval in timewarrior_parser.get_intervals()
    ]


@extract_fields(dict(spreadsheet_id=str))
def timewarrior_config(timewarrior_parser: TimeWarriorParser) -> dict:
    config = timewarrior_parser.get_config()
    spreadsheet_id = config.get_value("spreadsheet_id", None)

    if spreadsheet_id is None:
        raise ValueError(
            "Missing `spreasheet_id` config. Set it with `timew config spreadsheet_id ID`"
        )

    return dict(spreadsheet_id=spreadsheet_id)


def _is_tag_included(tags: list[str], target: str) -> bool:
    """Check if the `target` string is included in a tag.
    For example, target `foo` is in tag `foobar`.

    This allows some flexibility with regards to typos in tags.
    Since Timewarrior expects `+$TAG` while Timewarrior expects
    `$TAG`, uncessary `+` are sometime present in Timewarrior.
    """
    for tag in tags:
        if target in tag:
            return True
    return False


def _get_description(tags: list[str]) -> str:
    """Return the first tag containing more than one word.

    The Taskwarrior hook adds tags for task: project, tags, and description
    to the generated Timewarrior intervals. project and tags don't allow for
    whitespaces; only description does.

    Hits an edge case for single word descriptions. A single word task is
    a poorly written task and is uncommon.
    """
    for tag in tags:
        if len(tag.split(" ")) > 1:
            return tag
    return ""


def intervals_df(intervals: list[dict], must_include: str = "DW") -> pd.DataFrame:
    """Convert the Timewarrior parsed intervals to a dataframe.

    If `must_include`, check tags to ensure the string is present in a given tag.
    The default value is `DW`, which stands for DAGWorks, my current employer.

    Exclude intervals of 1 minute or less
    """
    df = pd.DataFrame.from_records(intervals)
    df = df.loc[df.duration > pd.Timedelta(minutes=1)]
    if must_include:
        df = df.loc[df.tags.apply(_is_tag_included, target=must_include)]

    df["week_day"] = df["date"].dt.weekday
    df["week_number"] = df["date"].dt.isocalendar().week
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["description"] = df.tags.apply(_get_description)

    return df[["date", "week_number", "week_day", "duration", "description"]]


def _deduplicate_items(items: list[str]) -> str:
    """Custom aggregation that reduces a list of strings
    to a set of unique items before joining them.
    """
    return "; ".join(set(items))


def daily_df(intervals_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate intervals daily to match the granularity of timesheet entries

    Note that the order of items in the `agg()` dict determines column orders.
    Also, we need to use `.reset_index()` to recover the `date` column.
    """
    return (
        intervals_df.groupby("date")
        .agg(
            dict(
                week_number="first",
                week_day="first",
                description=_deduplicate_items,
                duration="sum",
            )
        )
        .reset_index()
    )


def timesheet(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Converts seconds to hours. Then, convert to the number of quarter hours
    and round to nearest value.
    """
    daily_df["duration"] = daily_df["duration"].dt.total_seconds() / 3600
    daily_df["duration"] = (daily_df["duration"] / 0.25).round() * 0.25
    daily_df["weekly_cumulative"] = daily_df.groupby("week_number")["duration"].cumsum()
    return daily_df


def credentials() -> dict:
    credentials_path = pathlib.Path("~/.timewarrior/extensions/credentials.json").expanduser()
    return json.loads(credentials_path.read_text())


def google_service(credentials: dict) -> Resource:
    """Create a Google Resource used to interact with Google Sheets."""
    return build("sheets", "v4", credentials=Credentials.from_service_account_info(credentials))


def create_header_query(
    timesheet: pd.DataFrame,
    google_service: Resource,
    spreadsheet_id: str,
    sheet_id: str = DEFAULT_SHEET_ID,
) -> dict:
    """Query to create the header of our timesheet"""
    columns = timesheet.columns.to_list()
    header_query = (
        google_service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_id}!A1",
            valueInputOption="RAW",
            body={"values": [columns]},
        )
    )
    return header_query.execute()


def get_records_query(
    create_header_query: dict,
    google_service: Resource,
    spreadsheet_id: str,
    sheet_id: str = DEFAULT_SHEET_ID,
) -> dict:
    """Query to get the existing values in our timesheet.

    `create_header_query` is a dependency even though it doesn't
    pass any data because it needs to be executed first to enable
    parsing sheets values into a dataframe.

    Parsing the query results in a separate function, facilitates
    debugging by letting us inspect the query response.
    """
    query = (
        google_service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_id, majorDimension="ROWS")
    )
    return query.execute()


def existing_records(get_records_query: dict) -> pd.DataFrame:
    """Parse the existing records into a dataframe.
    The first row contains the header/columns, followed by daily
    timesheet records.
    """
    columns = get_records_query["values"][0]
    rows = get_records_query["values"][1:]
    return pd.DataFrame(rows, columns=columns)


def incremental_records(
    timesheet: pd.DataFrame,
    existing_records: pd.DataFrame,
    primary_key: str = "date",
) -> pd.DataFrame:
    """Check the `primary_key` in the current timesheet and the existing records
    and narrow it to new keys. Only return new records, sorted by `date`.

    Since `existing_records()` returns JSON-serializable types, we have to make sure
    both dataframes have the same type for the primary key. For example, `timesheet`
    would have column `date: Date`, but `existing_records` will have `date: str`
    """
    timesheet[primary_key] = timesheet[primary_key].astype(str)

    existing_keys = set(existing_records[primary_key])
    new_keys = set(timesheet[primary_key]).difference(existing_keys)
    return timesheet.loc[timesheet[primary_key].isin(new_keys)].sort_values("date")


def insert_records_query(
    incremental_records: pd.DataFrame,
    google_service: Resource,
    spreadsheet_id: str,
    sheet_id: str = DEFAULT_SHEET_ID,
) -> dict:
    """Query to insert new timesheet records in Google Sheets.

    Google expects row-major entries where each row is an iterable (i.e., list, tuple)
    Therefore, we need to unpack the dictionary. Doing `tuple(record.values())` ensures
    the order of the elements respects the order of the columns specified by `timesheet.columns.to_list()`
    in `create_header_query()`.
    """
    # convert Date objects to string to make JSON-serializable
    incremental_records["date"] = incremental_records["date"].astype(str)
    rows = [tuple(record.values()) for record in incremental_records.to_dict(orient="records")]

    # assumes less than 26 columns
    last_column_id = chr(64 + len(incremental_records.columns))
    query = (
        google_service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_id}!A2:{last_column_id}",
            valueInputOption="RAW",
            insertDataOption="OVERWRITE",
            body={"values": rows},
        )
    )
    query_results = query.execute()
    return query_results


def format_spreadsheet_query(
    insert_records_query: dict,
    google_service: Resource,
    spreadsheet_id: str,
    sheet_id: str = DEFAULT_SHEET_ID,
) -> dict:
    """Get all records after updating the timesheet and style rows
    by adding a border whenever the `week_number` changes
    """
    # use a node function directly
    records = get_records_query({}, google_service, spreadsheet_id, sheet_id)

    requests = []
    current_week = None
    for idx, record in enumerate(records["values"]):
        columns = records["values"][0]
        week_number_idx = columns.index("week_number")

        if current_week != record[week_number_idx]:
            current_week = record[week_number_idx]

            requests.append(
                {
                    "updateBorders": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": idx,
                            "endRowIndex": idx + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(columns),
                        },
                        "top": {"style": "SOLID", "width": 2},
                    }
                }
            )

    return (
        google_service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests})
        .execute()
    )


def command_output(
    format_spreadsheet_query: dict,
    incremental_records: pd.DataFrame,
    insert_records_query: dict,
) -> None:
    """Print back to the terminal the execution results.

    `format_spreadsheet_query()` is included to ensure it is executed.
    """
    records_uploaded = insert_records_query.get("updates", {}).get("updatedRows", 0)
    if records_uploaded:
        print(f"{records_uploaded=:}")
        print()
        print(incremental_records[["date", "duration", "weekly_cumulative"]])
    else:
        print("No new records to upload.")


if __name__ == "__main__":
    import pandas as pd

    import __main__
    from hamilton import driver

    # build dataflow
    dr = driver.Builder().with_modules(__main__).build()
    dr.display_all_functions("dag.png", orient="TB")
    # dr.execute(["command_output"])
