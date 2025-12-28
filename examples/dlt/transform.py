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

import textwrap

import dlt
import ibis
import ibis.expr.types as ir
import openai

from hamilton.function_modifiers import pipe, source, step
from hamilton.htypes import Collect, Parallelizable


def db_con(pipeline: dlt.Pipeline) -> ibis.BaseBackend:
    """Connect to the Ibis backend"""
    backend = ibis.connect(f"{pipeline.pipeline_name}.duckdb")
    ibis.set_backend(backend)
    return backend


def channel(selected_channels: list[str]) -> Parallelizable[str]:
    """Iterate over channels for which to load messages and replies"""
    for channel in selected_channels:
        yield channel


def _epoch_microseconds(timestamp: ir.TimestampColumn) -> ir.StringColumn:
    """Convert the timestamp value to a string with microsecond precision
    Required to meet the Slack format.
    """
    seconds_from_epoch = timestamp.epoch_seconds()
    microseconds = timestamp.microsecond() / int(10e5)
    return (seconds_from_epoch + microseconds).cast(str)


def channel_message(
    channel: str,
    db_con: ibis.BaseBackend,
    pipeline: dlt.Pipeline,
) -> ir.Table:
    """Load table containing parent messages of a channel.
    the timestamps `thread_ts` and `ts` are converted to strings.
    `thread_ts` is not None if the message has replies / started a thread. Otherwise,
    `thread_ts` == `ts`. Coalesce is used to fill these None values with `ts`

    Slack reference: https://api.slack.com/messaging/retrieving#finding_threads
    """
    return (
        db_con.table(
            f"{channel}_message",
            schema=pipeline.dataset_name,
            database=pipeline.pipeline_name,
        )
        .mutate(
            thread_ts=_epoch_microseconds(ibis._.thread_ts).cast(str),
            ts=_epoch_microseconds(ibis._.ts).cast(str),
        )
        .mutate(thread_ts=ibis.coalesce(ibis._.thread_ts, ibis._.ts))
    )


def channel_replies(
    channel: str,
    db_con: ibis.BaseBackend,
    pipeline: dlt.Pipeline,
) -> ir.Table:
    """Create table for replies"""
    return db_con.table(
        f"{channel}_replies_message",
        schema=pipeline.dataset_name,
        database=pipeline.pipeline_name,
    )


def channel_threads(
    channel_message: ir.Table,
    channel_replies: ir.Table,
) -> ir.Table:
    """Union of parent messages and replies. Sort by thread start, then message timestamp"""
    columns = ["channel", "thread_ts", "ts", "user", "text", "_dlt_load_id", "_dlt_id"]
    return ibis.union(
        channel_message.select(columns),
        channel_replies.select(columns),
    ).order_by([ibis._.thread_ts, ibis._.ts])


def channels_collection(channel_threads: Collect[ir.Table]) -> ir.Table:
    """Collect `channel_threads` for all channels"""
    return ibis.union(*channel_threads)


def _format_messages(threads: ir.Table) -> ir.Table:
    """Assign a user id per thread and prefix messages with it"""
    thread_user_id_expr = (ibis.dense_rank().over(order_by="user") + 1).cast(str)
    return threads.group_by("thread_ts").mutate(
        message=thread_user_id_expr.concat(": ", ibis._.text)
    )


def _aggregate_thread(threads: ir.Table) -> ir.Table:
    """Create threads as a single string by concatenating messages

    Functions decorates with `@ibis.udf` are loaded by the Ibis backend.
    They aren't meant to be called directly.
    ref: https://ibis-project.org/how-to/extending/builtin
    """

    @ibis.udf.agg.builtin(name="string_agg")
    def _string_agg(arg, sep: str = "\n ") -> str:
        raise NotImplementedError

    @ibis.udf.agg.builtin(name="array_agg")
    def _array_agg(arg) -> list[str]:
        raise NotImplementedError

    return threads.group_by("thread_ts").agg(
        thread=_string_agg(ibis._.message),
        num_messages=ibis._.count(),
        users=_array_agg(ibis._.user).unique(),
        _dlt_load_id=ibis._._dlt_load_id.max(),
        _dlt_id=_array_agg(ibis._._dlt_id),
    )


def summary_prompt() -> str:
    """LLM prompt to summarize Slack thread"""
    return textwrap.dedent(
        """Hamilton is an open source library to write dataflows in Python. It is used by developers for data engineering, data science, machine learning, and LLM workflows.
        Next is a discussion thread about Hamilton started by User1. Complete these tasks: identify the issue raised by User1, summarize the discussion, indicate if you think the issue was resolved.

        DISCUSSION THREAD
        {text}
        """
    )


def _summary(threads: ir.Table, prompt: str) -> ir.Table:
    """Generate a summary for each thread.
    Uses a scalar Python UDF executed by the backend.
    """

    @ibis.udf.scalar.python
    def _openai_completion_udf(
        text: str, prompt_template: str
    ) -> str:  # Ibis requires `str` type hint even if None is allowed
        """Fill `prompt` with `text` and use OpenAI chat completion.
        Returns None if:
            - `text` is empty
            - `content` is too long
            - OpenAI call fails
        """
        if len(text) == 0:
            return None

        content = prompt_template.format(text=text)

        if len(content) // 4 > 8191:
            return None

        client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": content}],
        )
        try:
            output = response.choices[0].message.content
        except Exception:
            output = None

        return output

    return threads.mutate(summary=_openai_completion_udf(threads.thread, prompt))


# @pipe operator facilitates managing the function/node namespace
@pipe(
    step(_format_messages), step(_aggregate_thread), step(_summary, prompt=source("summary_prompt"))
)
def threads(channels_collection: ir.Table) -> ir.Table:
    """Create `threads` table by formatting, aggregating messages,
    and generating summaries.
    """
    return channels_collection


def insert_threads(threads: ir.Table) -> int:
    """Save `threads` table and return row count."""
    db_con = ibis.get_backend()
    threads_table = db_con.create_table("threads", threads)
    db_con.insert("threads", threads)
    return int(threads_table.count().execute())
