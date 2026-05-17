"""Minimal in-process MCP-style server/client.

The Model Context Protocol is JSON-RPC 2.0 over a stream (stdio, SSE, websocket).
We re-implement just enough of it — message framing, tool/resource/prompt
registries, a synchronous in-process transport — so the four leaves in
``06-mcp/`` run with zero external dependencies. The notebooks reference
production MCP SDKs (`mcp`, `fastmcp`) but every code path here is
self-contained so CI is offline.

Spec references
---------------
* Protocol: https://modelcontextprotocol.io/
* JSON-RPC 2.0: https://www.jsonrpc.org/specification

Surface
-------
* :class:`Server` — register ``tools`` (callable + schema), ``resources``
  (URI -> content), and ``prompts`` (name -> template). Handles the canonical
  methods: ``initialize``, ``tools/list``, ``tools/call``, ``resources/list``,
  ``resources/read``, ``prompts/list``, ``prompts/get``.
* :class:`Client` — small wrapper around a ``Transport``. Provides
  ``list_tools``, ``call_tool``, ``list_resources``, ``read_resource``,
  ``list_prompts``, ``get_prompt``.
* :class:`InProcessTransport` — connects a client directly to a server via
  Python calls (no sockets needed).

Every leaf uses the same three canonical tools: ``search_corpus``,
``fetch_paper``, ``cite`` — sourced from the shared corpus loader so MCP
demos are apples-to-apples comparable with ``03-agentic-frameworks/``.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from shared.embedders import cosine_topk, hash_embed
from shared.loaders import load_corpus

DIMS = 256
SEED = 0
WORD_RE = re.compile(r"[A-Za-z0-9]+")

JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "agentic-ai-engineering/mcp"
SERVER_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Errors — JSON-RPC error codes
# ---------------------------------------------------------------------------


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    fn: Callable[..., Any]

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class Resource:
    uri: str
    name: str
    mime_type: str
    text: str
    description: str = ""

    def describe(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "mimeType": self.mime_type,
            "description": self.description,
        }


@dataclass
class Prompt:
    name: str
    description: str
    arguments: list[dict[str, Any]]
    render: Callable[..., list[dict[str, Any]]]

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


class Server:
    """Tiny MCP-compatible server. JSON-in / JSON-out via :meth:`handle`."""

    def __init__(self, name: str = SERVER_NAME, version: str = SERVER_VERSION) -> None:
        self.name = name
        self.version = version
        self.tools: dict[str, Tool] = {}
        self.resources: dict[str, Resource] = {}
        self.prompts: dict[str, Prompt] = {}
        self.audit_log: list[dict[str, Any]] = []
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "initialize": self._initialize,
            "tools/list": self._tools_list,
            "tools/call": self._tools_call,
            "resources/list": self._resources_list,
            "resources/read": self._resources_read,
            "prompts/list": self._prompts_list,
            "prompts/get": self._prompts_get,
        }

    # -- registration ----------------------------------------------------

    def add_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        fn: Callable[..., Any],
    ) -> None:
        self.tools[name] = Tool(
            name=name, description=description, input_schema=input_schema, fn=fn
        )

    def add_resource(self, resource: Resource) -> None:
        self.resources[resource.uri] = resource

    def add_prompt(self, prompt: Prompt) -> None:
        self.prompts[prompt.name] = prompt

    # -- request handling ------------------------------------------------

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        rid = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}
        if not isinstance(method, str):
            return _error_response(rid, INVALID_PARAMS, "method must be a string")
        handler = self._handlers.get(method)
        if handler is None:
            return _error_response(rid, METHOD_NOT_FOUND, f"unknown method {method!r}")
        self.audit_log.append({"id": rid, "method": method, "params": params})
        try:
            result = handler(params)
        except JsonRpcError as exc:
            return _error_response(rid, exc.code, exc.message, exc.data)
        except Exception as exc:  # pragma: no cover - defensive
            return _error_response(rid, INTERNAL_ERROR, repr(exc))
        return {"jsonrpc": JSONRPC_VERSION, "id": rid, "result": result}

    # -- canonical method implementations --------------------------------

    def _initialize(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {"name": self.name, "version": self.version},
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False, "subscribe": False},
                "prompts": {"listChanged": False},
            },
        }

    def _tools_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {"tools": [t.describe() for t in self.tools.values()]}

    def _tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or name not in self.tools:
            raise JsonRpcError(INVALID_PARAMS, f"unknown tool {name!r}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise JsonRpcError(INVALID_PARAMS, "arguments must be an object")
        try:
            result = self.tools[name].fn(**arguments)
        except TypeError as exc:
            raise JsonRpcError(INVALID_PARAMS, f"bad arguments: {exc}") from exc
        return {
            "content": [{"type": "text", "text": json.dumps(result, default=str)}],
            "isError": False,
        }

    def _resources_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {"resources": [r.describe() for r in self.resources.values()]}

    def _resources_read(self, params: dict[str, Any]) -> dict[str, Any]:
        uri = params.get("uri")
        if not isinstance(uri, str) or uri not in self.resources:
            raise JsonRpcError(INVALID_PARAMS, f"unknown resource {uri!r}")
        r = self.resources[uri]
        return {
            "contents": [
                {"uri": r.uri, "mimeType": r.mime_type, "text": r.text},
            ]
        }

    def _prompts_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {"prompts": [p.describe() for p in self.prompts.values()]}

    def _prompts_get(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or name not in self.prompts:
            raise JsonRpcError(INVALID_PARAMS, f"unknown prompt {name!r}")
        arguments = params.get("arguments") or {}
        messages = self.prompts[name].render(**arguments)
        return {"description": self.prompts[name].description, "messages": messages}


def _error_response(rid: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": rid, "error": err}


# ---------------------------------------------------------------------------
# Transport + Client
# ---------------------------------------------------------------------------


class Transport:
    """A transport is anything that ships a JSON-RPC request and returns the
    response. Real MCP uses stdio/SSE; this base class lets us swap them."""

    def send(self, request: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


class InProcessTransport(Transport):
    """Bypasses the wire; calls :meth:`Server.handle` directly."""

    def __init__(self, server: Server) -> None:
        self.server = server

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        # Round-trip via JSON to match the on-the-wire shape.
        wire = json.loads(json.dumps(request, default=str))
        return self.server.handle(wire)


@dataclass
class Client:
    transport: Transport
    initialized: bool = False
    server_info: dict[str, Any] = field(default_factory=dict)

    def _next_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def _call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request = {
            "jsonrpc": JSONRPC_VERSION,
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }
        response = self.transport.send(request)
        if "error" in response:
            raise JsonRpcError(
                response["error"].get("code", INTERNAL_ERROR),
                response["error"].get("message", "unknown error"),
                response["error"].get("data"),
            )
        return response.get("result")

    def initialize(self) -> dict[str, Any]:
        result = self._call(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "agentic-ai-engineering-client", "version": "0.1.0"},
            },
        )
        self.initialized = True
        self.server_info = result.get("serverInfo", {})
        return dict(result)

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._call("tools/list")["tools"])

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        result = self._call("tools/call", {"name": name, "arguments": arguments})
        for block in result.get("content", []):
            if block.get("type") == "text":
                try:
                    return json.loads(block["text"])
                except json.JSONDecodeError:
                    return block["text"]
        return result

    def list_resources(self) -> list[dict[str, Any]]:
        return list(self._call("resources/list")["resources"])

    def read_resource(self, uri: str) -> str:
        result = self._call("resources/read", {"uri": uri})
        for block in result.get("contents", []):
            if "text" in block:
                return str(block["text"])
        return ""

    def list_prompts(self) -> list[dict[str, Any]]:
        return list(self._call("prompts/list")["prompts"])

    def get_prompt(self, name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        result = self._call("prompts/get", {"name": name, "arguments": arguments})
        return list(result["messages"])


# ---------------------------------------------------------------------------
# Canonical corpus tools — shared by every MCP leaf
# ---------------------------------------------------------------------------


_DOCS = load_corpus()
_DOC_BY_ID = {d.arxiv_id: d for d in _DOCS}
_DOC_TEXTS = [d.title + ". " + d.abstract for d in _DOCS]
_DOC_VECS = hash_embed(_DOC_TEXTS, dims=DIMS, seed=SEED)


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) > 2}


def search_corpus(query: str, k: int = 3) -> list[dict[str, str]]:
    qv = hash_embed([query], dims=DIMS, seed=SEED)[0]
    idx, _ = cosine_topk(qv, _DOC_VECS, k=k)
    return [
        {
            "arxiv_id": _DOCS[i].arxiv_id,
            "title": _DOCS[i].title,
            "snippet": _DOCS[i].abstract[:240],
        }
        for i in idx
    ]


def fetch_paper(arxiv_id: str) -> dict[str, Any]:
    if arxiv_id not in _DOC_BY_ID:
        return {"error": f"document {arxiv_id!r} not found"}
    d = _DOC_BY_ID[arxiv_id]
    return {
        "arxiv_id": d.arxiv_id,
        "title": d.title,
        "abstract": d.abstract,
        "authors": d.authors,
        "year": d.year,
    }


def cite(arxiv_id: str, claim: str) -> dict[str, Any]:
    if arxiv_id not in _DOC_BY_ID:
        return {"supported": False, "evidence": ""}
    abstract = _DOC_BY_ID[arxiv_id].abstract
    claim_words = _words(claim)
    abs_words = _words(abstract)
    overlap = len(claim_words & abs_words) / max(len(claim_words), 1) if claim_words else 0.0
    return {
        "supported": overlap >= 0.3,
        "evidence": abstract[:240] if overlap >= 0.3 else "",
        "overlap_ratio": round(overlap, 3),
    }


SEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "free-text search"},
        "k": {"type": "integer", "minimum": 1, "default": 3},
    },
    "required": ["query"],
}

FETCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"arxiv_id": {"type": "string"}},
    "required": ["arxiv_id"],
}

CITE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "arxiv_id": {"type": "string"},
        "claim": {"type": "string"},
    },
    "required": ["arxiv_id", "claim"],
}


def build_corpus_server(
    *,
    with_resources: bool = False,
    with_prompts: bool = False,
) -> Server:
    """Return a server with the three canonical tools (+ optional extras)."""
    s = Server()
    s.add_tool(
        "search_corpus",
        "Hybrid search over the canonical arxiv corpus.",
        SEARCH_SCHEMA,
        search_corpus,
    )
    s.add_tool("fetch_paper", "Return the full record for an arxiv id.", FETCH_SCHEMA, fetch_paper)
    s.add_tool("cite", "Verify a claim against the named paper's abstract.", CITE_SCHEMA, cite)

    if with_resources:
        # Expose a resource per paper so resource-aware clients can browse.
        for d in _DOCS:
            s.add_resource(
                Resource(
                    uri=f"arxiv://{d.arxiv_id}",
                    name=d.title,
                    mime_type="text/plain",
                    text=f"# {d.title}\n\n{d.abstract}",
                    description=f"Arxiv paper {d.arxiv_id} ({d.year})",
                )
            )

    if with_prompts:

        def render_research(question: str = "") -> list[dict[str, Any]]:
            return [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": (
                            "You are a research assistant. Use the available "
                            "tools (search_corpus, fetch_paper, cite) and only "
                            "answer from the corpus. Cite every claim."
                        ),
                    },
                },
                {
                    "role": "user",
                    "content": {"type": "text", "text": question},
                },
            ]

        s.add_prompt(
            Prompt(
                name="research",
                description="Build a system+user message pair for a corpus research query.",
                arguments=[
                    {"name": "question", "description": "the user question", "required": True},
                ],
                render=render_research,
            )
        )
    return s


# ---------------------------------------------------------------------------
# Convenience: tiny agent that consumes an MCP client
# ---------------------------------------------------------------------------


@dataclass
class AgentStep:
    role: Literal["tool_call", "final"]
    name: str | None = None
    arguments: dict[str, Any] | None = None
    result_summary: str | None = None
    content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"role": self.role}
        if self.role == "tool_call":
            out["name"] = self.name
            out["arguments"] = self.arguments
            out["result_summary"] = self.result_summary
        else:
            out["content"] = self.content
        return out


def mcp_agent_solve(client: Client, question: str) -> dict[str, Any]:
    """Deterministic, offline agent that drives any MCP server with our schema.

    Used by the client-in-agent eval. Calls ``search_corpus`` →
    ``fetch_paper`` (top hit) → ``cite`` → emits a final citation-rich
    answer. Returns ``{trace, answer}`` matching the agentic-frameworks
    trace shape so snapshots compare cleanly.
    """
    steps: list[AgentStep] = []
    hits = client.call_tool("search_corpus", {"query": question, "k": 2})
    steps.append(
        AgentStep(
            role="tool_call",
            name="search_corpus",
            arguments={"query": question, "k": 2},
            result_summary=f"hits={[h['arxiv_id'] for h in hits]}",
        )
    )
    if not hits:
        steps.append(AgentStep(role="final", content="I don't know based on the provided context."))
        return {"trace": [s.to_dict() for s in steps], "answer": steps[-1].content}

    top_id = hits[0]["arxiv_id"]
    paper = client.call_tool("fetch_paper", {"arxiv_id": top_id})
    steps.append(
        AgentStep(
            role="tool_call",
            name="fetch_paper",
            arguments={"arxiv_id": top_id},
            result_summary=f"title={paper.get('title')!r}",
        )
    )
    head = paper.get("abstract", "").split(".")[0]
    answer = f"[{top_id}] {head}."
    citation = client.call_tool("cite", {"arxiv_id": top_id, "claim": answer})
    steps.append(
        AgentStep(
            role="tool_call",
            name="cite",
            arguments={"arxiv_id": top_id, "claim": answer[:120]},
            result_summary=f"supported={citation['supported']} overlap={citation['overlap_ratio']}",
        )
    )
    steps.append(AgentStep(role="final", content=answer))
    return {"trace": [s.to_dict() for s in steps], "answer": answer}


__all__ = [
    "CITE_SCHEMA",
    "FETCH_SCHEMA",
    "PROTOCOL_VERSION",
    "SEARCH_SCHEMA",
    "Client",
    "InProcessTransport",
    "JsonRpcError",
    "Prompt",
    "Resource",
    "Server",
    "Tool",
    "Transport",
    "build_corpus_server",
    "cite",
    "fetch_paper",
    "mcp_agent_solve",
    "search_corpus",
]
