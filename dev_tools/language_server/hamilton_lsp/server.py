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

import inspect
import re
from typing import Type

from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    CompletionItem,
    CompletionItemKind,
    CompletionItemLabelDetails,
    CompletionList,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbolParams,
    Location,
    Position,
    Range,
    SymbolInformation,
    SymbolKind,
    VersionedTextDocumentIdentifier,
)
from pygls.server import LanguageServer

from hamilton import ad_hoc_utils
from hamilton.graph import FunctionGraph, create_graphviz_graph
from hamilton.graph_types import HamiltonGraph
from hamilton_lsp import __version__


def _type_to_string(type_: Type):
    """Return the full path of type, but may not be accessible from document
    For example, `pandas.core.series.Series` while document defines `pandas as pd`
    """
    if type_.__module__ == "builtins":
        type_string = str(type_.__name__)
    else:
        type_string = f"{str(type_.__module__)}.{str(type_.__name__)}"

    return type_string


def _parse_function_tokens(source: str) -> dict[str, str]:
    """Get a more precise type definition"""
    # re.DOTALL allows for multiline definition
    FUNCTION_PATTERN = re.compile(r"def\s+(\w+)\((.*?)\)\s*->\s*([^\n:]+)", re.DOTALL)

    # {function_name: type}
    results = {}
    for matching in FUNCTION_PATTERN.finditer(source):
        function_name = matching.group(1)
        return_type = matching.group(3)
        results[function_name] = return_type

        argument_string = matching.group(2)
        if argument_string:
            for arg_with_type in argument_string.split(","):
                arg, _, arg_type = arg_with_type.strip().partition(":")
                arg_type, _, _ = arg_type.partition("=")
                results[arg.strip()] = arg_type.strip()

    return results


class HamiltonLanguageServer(LanguageServer):
    CMD_VIEW_REQUEST = "lsp-view-request"
    CMD_VIEW_RESPONSE = "lsp-view-response"

    def __init__(self, server: str = "HamiltonServer", version: str = __version__, loop=None):
        super().__init__(server, version, loop=loop, max_workers=2)

        self.active_uri: str = ""
        self.active_version: str = ""
        self.orientation = "LR"
        self.node_locations = {}
        self.fn_graph = FunctionGraph({}, {})
        self.h_graph = HamiltonGraph.from_graph(self.fn_graph)

    # def get_range(self, node):
    #     FUNCTION = re.compile(r"^fn ([a-z]\w+)\(")
    #     ARGUMENT = re.compile(r"(?P<name>\w+): (?P<type>\w+)")

    #     origin = node.originating_functions[0]
    #     name = node.name
    #     # get node type icon (function, inputs, config, materializers)
    #     # get location
    #     lines, linenum = inspect.getsourcelines(origin)

    #     for incr, line in enumerate(lines):
    #         if (match := FUNCTION.match(line)) is not None:
    #             symbol_name = match.group(1)
    #             if name in symbol_name:
    #                 start_char = match.start() + line.find(name)
    #                 return Range(
    #                     start=Position(line=linenum+incr, character=start_char),
    #                     end=Position(line=linenum+incr, character=start_char + len(name)),
    #                 )


def register_server_features(ls: HamiltonLanguageServer) -> HamiltonLanguageServer:
    @ls.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(server: HamiltonLanguageServer, params: DidChangeTextDocumentParams):
        """try to build the dataflow and cache it on the server by creating
        a temporary module from the document's source code
        """
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)
        server.active_uri = uri

        try:
            config = {}
            module = ad_hoc_utils.module_from_source(document.source)
            fn_graph = FunctionGraph.from_modules(module, config=config)
            h_graph = HamiltonGraph.from_graph(fn_graph)
            # store the updated HamiltonGraph on server state
            server.fn_graph = fn_graph
            server.h_graph = h_graph
        except BaseException:
            pass

        # refresh the visualization if new graph version
        if server.active_version != server.h_graph.version:
            server.active_version = server.h_graph.version
            hamilton_view(server, [{}])

    @ls.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(server: HamiltonLanguageServer, params: DidOpenTextDocumentParams):
        """trigger the did_change() event"""
        did_change(
            server,
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(
                    version=0,
                    uri=params.text_document.uri,
                ),
                content_changes=[],
            ),
        )

    @ls.feature(TEXT_DOCUMENT_COMPLETION)  # , CompletionOptions(trigger_characters=["(", ","]))
    def on_completion(server: HamiltonLanguageServer, params: CompletionParams) -> CompletionList:
        """Return completion items based on the cached dataflow nodes name and type."""
        uri = params.text_document.uri
        document = server.workspace.get_document(uri)

        tokens = _parse_function_tokens(document.source)

        # could be refactored to a single loop, but this logic might be reused elsewhere
        local_node_types = {}
        for node in server.h_graph.nodes:
            origin = node.originating_functions[0]

            origin_name = getattr(origin, "__original_name__", origin.__name__)
            type_ = tokens.get(origin_name, _type_to_string(node.type))
            local_node_types[node.name] = type_

        return CompletionList(
            is_incomplete=False,
            items=[
                CompletionItem(
                    label=node.name,
                    label_details=CompletionItemLabelDetails(
                        detail=f" {local_node_types[node.name]}",
                        description="Node",
                    ),
                    kind=CompletionItemKind(3),  # 3 is the enum for `Function` kind
                    documentation=node.documentation,
                    insert_text=f"{node.name}: {local_node_types[node.name]}",
                )
                for node in server.h_graph.nodes
            ],
        )

    @ls.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbols(
        server: HamiltonLanguageServer, params: DocumentSymbolParams
    ) -> list[SymbolInformation]:
        symbols = []

        for node in server.h_graph.nodes:
            origin = node.originating_functions[0]
            name = node.name
            # get node type icon (function, inputs, config, materializers)
            node_kind = SymbolKind.Function
            if node.is_external_input:
                node_kind = SymbolKind.Field

            # get location
            _, starting_line = inspect.getsourcelines(origin)
            loc = Location(
                uri=params.text_document.uri,
                range=Range(
                    start=Position(line=starting_line - 1, character=0),
                    end=Position(line=starting_line, character=0),
                ),
            )
            server.node_locations[name] = loc

            # create symbol
            symbol = SymbolInformation(
                name=name,
                kind=node_kind,
                location=loc,
                container_name="Hamilton",
            )
            symbols.append(symbol)

        return symbols

    # @ls.feature(TEXT_DOCUMENT_REFERENCES)
    # def find_references(
    #     server: HamiltonLanguageServer,
    #     params: ReferenceParams
    # ) -> list[Location]:
    #     doc = ls.workspace.get_text_document(params.text_document.uri)

    #     input_position = params.position
    #     if not server.node_locations:
    #         server.send_notification(TEXT_DOCUMENT_DOCUMENT_SYMBOL, DocumentSymbolParams(params.text_document))

    #     word = doc.word_at_position(input_position)
    #     server.show_message_log(f"{word}")

    #     # server.show_message_log(input_node)
    #     depend_on_input = []
    #     for node in server.h_graph.nodes:
    #         dependencies = [*node.optional_dependencies, *node.required_dependencies]
    #         for dep in dependencies:
    #             if word != dep:
    #                 continue
    #             depend_on_input.append(node.name)

    #     return [server.node_locations[name] for name in depend_on_input]

    @ls.thread()
    @ls.command(HamiltonLanguageServer.CMD_VIEW_REQUEST)
    def hamilton_view(server: HamiltonLanguageServer, args: list[dict]):
        """View the cached dataflow and send the graphviz string to the extension host."""
        params = args[0]

        if params.get("rotate"):
            if server.orientation == "LR":
                server.orientation = "TB"
            else:
                server.orientation = "LR"

        dot = create_graphviz_graph(
            nodes=set(server.fn_graph.get_nodes()),
            comment="vscode-dataflow",
            node_modifiers=dict(),
            strictly_display_only_nodes_passed_in=True,
            graphviz_kwargs=dict(
                graph_attr=dict(bgcolor="transparent"),
                edge_attr=dict(color="white"),
            ),
            orient=server.orientation,
            config={},
        )

        server.send_notification(
            HamiltonLanguageServer.CMD_VIEW_RESPONSE, dict(uri=server.active_uri, dot=dot.source)
        )

    return ls
