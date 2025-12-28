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
import uuid
from typing import Tuple

import falkordb
import openai
from burr.core import Application, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.tracking import LocalTrackingClient
from falkordb import FalkorDB
from graph_schema import graph_schema


# --- helper functions
def schema_to_prompt(schema):
    prompt = "The Knowledge graph contains nodes of the following types:\n"

    for node in schema["nodes"]:
        lbl = node
        node = schema["nodes"][node]
        if len(node["attributes"]) > 0:
            prompt += f"The {lbl} node type has the following set of attributes:\n"
            for attr in node["attributes"]:
                t = node["attributes"][attr]["type"]
                prompt += f"The {attr} attribute is of type {t}\n"
        else:
            prompt += f"The {node} node type has no attributes:\n"

    prompt += "In addition the Knowledge graph contains edge of the following types:\n"

    for edge in schema["edges"]:
        rel = edge
        edge = schema["edges"][edge]
        if len(edge["attributes"]) > 0:
            prompt += f"The {rel} edge type has the following set of attributes:\n"
            for attr in edge["attributes"]:
                t = edge["attributes"][attr]["type"]
                prompt += f"The {attr} attribute is of type {t}\n"
        else:
            prompt += f"The {rel} edge type has no attributes:\n"

        prompt += f"The {rel} edge connects the following entities:\n"
        for conn in edge["connects"]:
            src = conn[0]
            dest = conn[1]
            prompt += f"{src} is connected via {rel} to {dest}, (:{src})-[:{rel}]->(:{dest})\n"

    return prompt


def set_inital_chat_history(schema_prompt: str) -> list[dict]:
    SYSTEM_MESSAGE = "You are a Cypher expert with access to a directed knowledge graph\n"
    SYSTEM_MESSAGE += schema_prompt
    SYSTEM_MESSAGE += (
        "Query the knowledge graph to extract relevant information to help you answer the users "
        "questions, base your answer only on the context retrieved from the knowledge graph, "
        "do not use preexisting knowledge."
    )
    SYSTEM_MESSAGE += (
        "For example to find out if two fighters had fought each other e.g. did Conor McGregor "
        "every compete against Jose Aldo issue the following query: "
        "MATCH (a:Fighter)-[]->(f:Fight)<-[]-(b:Fighter) WHERE a.Name = 'Conor McGregor' AND "
        "b.Name = 'Jose Aldo' RETURN a, b\n"
    )

    messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
    return messages


# ---  tools


def run_cypher_query(graph, query):
    try:
        results = graph.ro_query(query).result_set
    except Exception:
        results = {"error": "Query failed please try a different variation of this query"}

    if len(results) == 0:
        results = {
            "error": "The query did not return any data, please make sure you're using the right edge "
            "directions and you're following the correct graph schema"
        }

    return str(results)


run_cypher_query_tool_description = {
    "type": "function",
    "function": {
        "name": "run_cypher_query",
        "description": "Runs a Cypher query against the knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to execute",
                },
            },
            "required": ["query"],
        },
    },
}


# --- actions


@action(
    reads=[],
    writes=["question", "chat_history"],
)
def human_converse(state: State, user_question: str) -> Tuple[dict, State]:
    """Human converse step -- make sure we get input, and store it as state."""
    new_state = state.update(question=user_question)
    new_state = new_state.append(chat_history={"role": "user", "content": user_question})
    return {"question": user_question}, new_state


@action(
    reads=["question", "chat_history"],
    writes=["chat_history", "tool_calls"],
)
def AI_create_cypher_query(state: State, client: openai.Client) -> tuple[dict, State]:
    """AI step to create the cypher query."""
    messages = state["chat_history"]
    # Call the function
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        tools=[run_cypher_query_tool_description],
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    new_state = state.append(chat_history=response_message.to_dict())
    tool_calls = response_message.tool_calls
    if tool_calls:
        new_state = new_state.update(tool_calls=tool_calls)
    return {"ai_response": response_message.content, "usage": response.usage.to_dict()}, new_state


@action(
    reads=["tool_calls", "chat_history"],
    writes=["tool_calls", "chat_history"],
)
def tool_call(state: State, graph: falkordb.Graph) -> Tuple[dict, State]:
    """Tool call step -- execute the tool call."""
    tool_calls = state.get("tool_calls", [])
    new_state = state
    result = {"tool_calls": []}
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        assert function_name == "run_cypher_query"
        function_args = json.loads(tool_call.function.arguments)
        function_response = run_cypher_query(graph, function_args.get("query"))
        new_state = new_state.append(
            chat_history={
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
        )
        result["tool_calls"].append({"tool_call_id": tool_call.id, "response": function_response})
    new_state = new_state.update(tool_calls=[])
    return result, new_state


@action(
    reads=["chat_history"],
    writes=["chat_history"],
)
def AI_generate_response(state: State, client: openai.Client) -> tuple[dict, State]:
    """AI step to generate the response."""
    messages = state["chat_history"]
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
    )  # get a new response from the model where it can see the function response
    response_message = response.choices[0].message
    new_state = state.append(chat_history=response_message.to_dict())
    return {"ai_response": response_message.content, "usage": response.usage.to_dict()}, new_state


def build_application(
    db_client: FalkorDB, graph_name: str, application_run_id: str, openai_client: openai.OpenAI
) -> Application:
    """Builds the application."""
    # get the graph
    graph = db_client.select_graph(graph_name)
    # get schema
    schema = graph_schema(graph)
    # create a prompt from it
    schema_prompt = schema_to_prompt(schema)
    # set the initial chat history
    base_messages = set_inital_chat_history(schema_prompt)

    tracker = LocalTrackingClient("ufc-falkor")
    # create graph
    burr_application = (
        ApplicationBuilder()
        .with_actions(  # define the actions
            AI_create_cypher_query.bind(client=openai_client),
            tool_call.bind(graph=graph),
            AI_generate_response.bind(client=openai_client),
            human_converse,
        )
        .with_transitions(  # define the edges between the actions based on state conditions
            ("human_converse", "AI_create_cypher_query", default),
            ("AI_create_cypher_query", "tool_call", expr("len(tool_calls)>0")),
            ("AI_create_cypher_query", "human_converse", default),
            ("tool_call", "AI_generate_response", default),
            ("AI_generate_response", "human_converse", default),
        )
        .with_identifiers(app_id=application_run_id)
        .with_state(  # initial state
            **{"chat_history": base_messages, "tool_calls": []},
        )
        .with_entrypoint("human_converse")
        .with_tracker(tracker)
        .build()
    )
    return burr_application


if __name__ == "__main__":
    print(
        """Run
    > burr
    in another terminal to see the UI at http://localhost:7241
    """
    )
    _client = openai.OpenAI()
    _db_client = FalkorDB(host="localhost", port=6379)
    _graph_name = "UFC"
    _app_run_id = str(uuid.uuid4())  # this is a unique identifier for the application run
    # build the app
    _app = build_application(_db_client, _graph_name, _app_run_id, _client)

    # visualize the app
    _app.visualize(output_file_path="ufc-burr", include_conditions=True, view=True, format="png")

    # run it
    while True:
        question = input("What can I help you with?\n")
        if question == "exit":
            break
        action, _, state = _app.run(
            halt_before=["human_converse"],
            inputs={"user_question": question},
        )
        print(f"AI: {state['chat_history'][-1]['content']}\n")
