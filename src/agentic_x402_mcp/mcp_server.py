"""Zero-dependency Model Context Protocol (MCP) stdio JSON-RPC 2.0 server."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, TextIO, Tuple, Union

__version__ = "1.1.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

DATASET_FILES: Dict[str, str] = {
    "endpoints": "x402_endpoints_benchmark_2026.csv",
    "guardrails": "dev_tooling_guardrails_benchmark_2026.csv",
    "catalog": "gumroad_bundles_catalog_2026.csv",
}

_MAX_LIMIT = 100
_DEFAULT_LIMIT = 20

_TOOL_ALLOWED_ARGS: Dict[str, FrozenSet[str]] = {
    "x402_list_endpoints_benchmark": frozenset(
        {"network", "price_band", "verified", "is_json_x402", "query", "limit", "offset"}
    ),
    "x402_list_guardrails_benchmark": frozenset(
        {"benchmark_domain", "metric_key", "query", "limit", "offset"}
    ),
    "x402_list_apify_kits_catalog": frozenset(
        {
            "channel",
            "billing_model",
            "in_manifest_only",
            "slug",
            "max_price_usd",
            "query",
            "limit",
            "offset",
        }
    ),
    "x402_verify_dataset_integrity": frozenset({"dataset", "include_headers"}),
}


def _validate_dataset_dir(candidate: Path) -> Path:
    """Validate that candidate is a directory containing all allowlisted CSV datasets."""
    root = candidate.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {candidate}")
    for filename in DATASET_FILES.values():
        target = root / filename
        if target.is_symlink():
            raise ValueError(f"Symlinked dataset file rejected: {target}")
        if not target.is_file():
            raise FileNotFoundError(f"Missing required dataset file: {target}")
        if target.resolve().parent != root:
            raise ValueError(f"Dataset file escapes root directory: {target}")
    return root


def resolve_dataset_root(dataset_dir: Optional[Union[Path, str]] = None) -> Path:
    """Resolve and validate the dataset directory without environment lookups."""
    if dataset_dir is not None:
        return _validate_dataset_dir(Path(dataset_dir))

    module_path = Path(__file__).resolve()
    candidates: List[Path] = []
    if len(module_path.parents) > 2:
        candidates.append(module_path.parents[2])
    candidates.append(module_path.parent / "data")

    errors: List[str] = []
    for candidate in candidates:
        try:
            return _validate_dataset_dir(candidate)
        except (FileNotFoundError, ValueError) as exc:
            errors.append(str(exc))

    raise FileNotFoundError(
        "Unable to locate benchmark CSV datasets in repository root or package data: "
        + "; ".join(errors)
    )


def _resolve_dataset_file(dataset_root: Path, dataset_key: str) -> Path:
    """Resolve an allowlisted dataset key inside the validated dataset root."""
    filename = DATASET_FILES.get(dataset_key)
    if filename is None:
        raise ValueError(f"Unknown dataset key: {dataset_key}")
    root_resolved = dataset_root.resolve()
    target = root_resolved / filename
    if target.is_symlink():
        raise ValueError(f"Symlinked dataset file rejected: {target}")
    if not target.is_file() or target.resolve().parent != root_resolved:
        raise FileNotFoundError(f"Dataset file unavailable inside root: {filename}")
    return target


def _parse_csv_bytes(raw_bytes: bytes) -> Tuple[List[str], List[Dict[str, str]], bool]:
    """Parse raw UTF-8 CSV bytes into headers, row dicts, and a rectangularity flag."""
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    rows_raw = list(reader)
    if not rows_raw:
        return [], [], False

    headers = [col.strip() for col in rows_raw[0]]
    width = len(headers)
    rectangular = width > 0 and all(len(row) == width for row in rows_raw[1:])
    records: List[Dict[str, str]] = []
    for raw_row in rows_raw[1:]:
        padded = list(raw_row[:width]) + [""] * max(0, width - len(raw_row))
        records.append(dict(zip(headers, padded)))
    return headers, records, rectangular


def _read_csv_snapshot(path: Path) -> Tuple[bytes, List[str], List[Dict[str, str]], bool]:
    """Read raw dataset bytes once and parse CSV rows from the exact same snapshot."""
    raw_bytes = path.read_bytes()
    headers, records, rectangular = _parse_csv_bytes(raw_bytes)
    return raw_bytes, headers, records, rectangular


def _validate_allowed_keys(tool_name: str, args: Dict[str, Any]) -> None:
    allowed = _TOOL_ALLOWED_ARGS.get(tool_name, frozenset())
    unknown = sorted(set(args.keys()) - allowed)
    if unknown:
        raise ValueError(
            f"Unsupported argument(s) for {tool_name}: {', '.join(unknown)}"
        )


def _parse_bool_arg(value: Any, field_name: str) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        norm = value.strip().lower()
        if norm == "true":
            return True
        if norm == "false":
            return False
    raise ValueError(f"Argument '{field_name}' must be a boolean")


def _parse_int_arg(value: Any, default: int, field_name: str) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Argument '{field_name}' must be an integer")
    return value


def _clamp_pagination(args: Dict[str, Any]) -> Tuple[int, int]:
    raw_limit = _parse_int_arg(args.get("limit"), _DEFAULT_LIMIT, "limit")
    raw_offset = _parse_int_arg(args.get("offset"), 0, "offset")
    limit = max(1, min(_MAX_LIMIT, raw_limit))
    offset = max(0, raw_offset)
    return limit, offset


def _parse_optional_str(args: Dict[str, Any], field_name: str) -> Optional[str]:
    val = args.get(field_name)
    if val is None:
        return None
    if not isinstance(val, str):
        raise ValueError(f"Argument '{field_name}' must be a string")
    stripped = val.strip()
    return stripped if stripped else None


def _parse_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"Argument '{field_name}' must be numeric")
    if isinstance(value, Decimal):
        dec = value
    elif isinstance(value, (int, float, str)):
        raw = str(value).strip()
        if not raw:
            raise ValueError(f"Argument '{field_name}' must not be empty")
        try:
            dec = Decimal(raw)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc
    else:
        raise ValueError(f"Argument '{field_name}' must be numeric")
    if not dec.is_finite():
        raise ValueError(f"Non-finite decimal value for '{field_name}'")
    return dec


def _reject_json_constant(constant: str) -> Any:
    raise ValueError(f"Non-standard JSON numeric constant rejected: {constant}")


def _parse_json_line(line: str) -> Any:
    return json.loads(
        line,
        parse_float=Decimal,
        parse_constant=_reject_json_constant,
    )


def _is_valid_jsonrpc_id(msg_id: Any) -> bool:
    if msg_id is None:
        return True
    if isinstance(msg_id, bool):
        return False
    return isinstance(msg_id, (str, int, float, Decimal))


def _format_endpoint_row(row: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(row)
    raw_id = row.get("row_id", "").strip()
    if raw_id.isdigit():
        out["row_id"] = int(raw_id)
    raw_json_flag = row.get("is_json_x402", "").strip().lower()
    if raw_json_flag in ("true", "false"):
        out["is_json_x402"] = raw_json_flag == "true"
    return out


def _format_catalog_row(row: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(row)
    for int_col in (
        "pack_rank",
        "price_atomic_usdc_6dec",
        "file_count",
        "zip_bytes",
        "uncompressed_bytes",
    ):
        raw = row.get(int_col, "").strip()
        if raw.isdigit():
            out[int_col] = int(raw)
    raw_manifest = row.get("in_gumroad_13_pack_manifest", "").strip().lower()
    if raw_manifest in ("true", "false"):
        out["in_gumroad_13_pack_manifest"] = raw_manifest == "true"
    return out


def _count_by_key(rows: Sequence[Dict[str, str]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        val = row.get(key, "")
        counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items()))


def _tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "x402_list_endpoints_benchmark",
            "description": (
                "Filter, search, and paginate rows from x402_endpoints_benchmark_2026.csv "
                "(51 deduplicated CDP Bazaar and reference x402 micro-payment endpoints across "
                "Base eip155:8453 and BNB Chain eip155:56)."
            ),
            "annotations": {
                "title": "List x402 Endpoints Benchmark",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "Exact CAIP-2 network ID filter (e.g., eip155:8453 or eip155:56).",
                    },
                    "price_band": {
                        "type": "string",
                        "description": "Exact price band filter (e.g., <$0.01, $0.01-$0.10, non-usd-asset, unknown).",
                    },
                    "verified": {
                        "type": "string",
                        "description": "Exact verification status filter (e.g., handshake, listing-only, http_402_non_x402).",
                    },
                    "is_json_x402": {
                        "type": "boolean",
                        "description": "Filter by whether the endpoint exposes structured JSON x402 metadata.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Case-insensitive substring search across url, operator, asset, notes, and discovered_via.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": _DEFAULT_LIMIT,
                        "minimum": 1,
                        "maximum": _MAX_LIMIT,
                        "description": "Maximum rows to return (clamped to 1..100).",
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0,
                        "minimum": 0,
                        "description": "Pagination offset into matched rows.",
                    },
                },
            },
        },
        {
            "name": "x402_list_guardrails_benchmark",
            "description": (
                "Filter, search, and paginate empirical engineering and guardrail benchmark rows "
                "from dev_tooling_guardrails_benchmark_2026.csv (x402 census metrics, 52 code-mistake "
                "rules, Web3 bug bounty radar counts, and macOS arm64 CLI compatibility)."
            ),
            "annotations": {
                "title": "List Dev Tooling & Guardrails Benchmark",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "benchmark_domain": {
                        "type": "string",
                        "description": "Exact benchmark domain filter (e.g., x402_census, code_mistakes_guard, gumroad_catalog).",
                    },
                    "metric_key": {
                        "type": "string",
                        "description": "Case-insensitive substring filter on metric_key.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Case-insensitive substring search across benchmark_domain, metric_key, and source_file.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": _DEFAULT_LIMIT,
                        "minimum": 1,
                        "maximum": _MAX_LIMIT,
                        "description": "Maximum rows to return (clamped to 1..100).",
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0,
                        "minimum": 0,
                        "description": "Pagination offset into matched rows.",
                    },
                },
            },
        },
        {
            "name": "x402_list_apify_kits_catalog",
            "description": (
                "Filter, search, and paginate rows from gumroad_bundles_catalog_2026.csv covering "
                "all 16 Apify & developer kit bundles with exact Decimal USD prices, 6-decimal atomic "
                "USDC amounts, byte sizes, and SHA-256 checksums."
            ),
            "annotations": {
                "title": "List Apify Kits & Bundles Catalog",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Exact distribution channel filter (e.g., gumroad_2026_flagship, gumroad_v1_kit, apify_store_mirror).",
                    },
                    "billing_model": {
                        "type": "string",
                        "description": "Exact billing model filter (e.g., one_time_gumroad, monthly_subscription_or_kit).",
                    },
                    "in_manifest_only": {
                        "type": "boolean",
                        "description": "Filter by membership in the 13-pack flagship manifest.",
                    },
                    "slug": {
                        "type": "string",
                        "description": "Case-insensitive substring filter on bundle slug.",
                    },
                    "max_price_usd": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Maximum recommended_price_usd filter evaluated with exact Decimal arithmetic.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Case-insensitive substring search across slug, title, channel, and relative_dist_path.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": _DEFAULT_LIMIT,
                        "minimum": 1,
                        "maximum": _MAX_LIMIT,
                        "description": "Maximum rows to return (clamped to 1..100).",
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0,
                        "minimum": 0,
                        "description": "Pagination offset into matched rows.",
                    },
                },
            },
        },
        {
            "name": "x402_verify_dataset_integrity",
            "description": (
                "Verify that the committed benchmark CSV datasets exist inside the validated dataset "
                "root and compute deterministic row counts, column headers, byte sizes, and SHA-256 digests."
            ),
            "annotations": {
                "title": "Verify Benchmark Dataset Integrity",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "dataset": {
                        "type": "string",
                        "enum": ["all", "endpoints", "guardrails", "catalog"],
                        "default": "all",
                        "description": "Verify all 3 CSV datasets or one allowlisted dataset key.",
                    },
                    "include_headers": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include exact CSV column header names in each dataset report.",
                    },
                },
            },
        },
    ]


class AgenticX402MCPServer:
    """Line-delimited JSON-RPC 2.0 MCP server over stdio."""

    def __init__(self, dataset_dir: Optional[Union[Path, str]] = None) -> None:
        self.dataset_root = resolve_dataset_root(dataset_dir)

    def handle_request(self, message: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(message, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request"},
            }

        has_id_member = "id" in message
        msg_id = message.get("id")
        if has_id_member and not _is_valid_jsonrpc_id(msg_id):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request: invalid id type"},
            }

        err_id = msg_id if has_id_member else None
        if message.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": err_id,
                "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"},
            }

        method = message.get("method")
        if not isinstance(method, str) or not method:
            return {
                "jsonrpc": "2.0",
                "id": err_id,
                "error": {"code": -32600, "message": "Invalid Request: missing method"},
            }

        params = message.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            if not has_id_member:
                return None
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32602, "message": "Invalid params: expected object"},
            }

        # JSON-RPC 2.0 notifications omit the `id` member and receive no response.
        if not has_id_member:
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "agentic-x402-apify-kits",
                        "version": __version__,
                    },
                },
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": _tool_definitions()},
            }

        if method == "tools/call":
            tool_name = params.get("name")
            if not isinstance(tool_name, str) or not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": "Error: Missing tool name"}],
                        "isError": True,
                    },
                }
            raw_args = params.get("arguments")
            if raw_args is None:
                raw_args = {}
            if not isinstance(raw_args, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": "Error: Tool arguments must be a JSON object"}
                        ],
                        "isError": True,
                    },
                }
            try:
                output = self._dispatch_tool(tool_name, raw_args)
            except (
                ValueError,
                FileNotFoundError,
                OSError,
                UnicodeDecodeError,
                csv.Error,
                InvalidOperation,
            ) as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {exc}"}],
                        "isError": True,
                    },
                }
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(output, indent=2, ensure_ascii=False),
                        }
                    ],
                    "isError": False,
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def _dispatch_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name not in _TOOL_ALLOWED_ARGS:
            raise ValueError(f"Unknown MCP tool: {name}")
        _validate_allowed_keys(name, args)

        if name == "x402_list_endpoints_benchmark":
            return self._list_endpoints_benchmark(args)
        if name == "x402_list_guardrails_benchmark":
            return self._list_guardrails_benchmark(args)
        if name == "x402_list_apify_kits_catalog":
            return self._list_apify_kits_catalog(args)
        return self._verify_dataset_integrity(args)

    def _list_endpoints_benchmark(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit, offset = _clamp_pagination(args)
        network = _parse_optional_str(args, "network")
        price_band = _parse_optional_str(args, "price_band")
        verified = _parse_optional_str(args, "verified")
        is_json_x402 = _parse_bool_arg(args.get("is_json_x402"), "is_json_x402")
        query = _parse_optional_str(args, "query")

        path = _resolve_dataset_file(self.dataset_root, "endpoints")
        _, headers, rows, _ = _read_csv_snapshot(path)

        matched: List[Dict[str, str]] = []
        query_lower = query.lower() if query is not None else None
        for row in rows:
            if network is not None and row.get("network", "").strip().lower() != network.lower():
                continue
            if price_band is not None and row.get("price_band", "").strip().lower() != price_band.lower():
                continue
            if verified is not None and row.get("verified", "").strip().lower() != verified.lower():
                continue
            if is_json_x402 is not None:
                row_flag = row.get("is_json_x402", "").strip().lower() == "true"
                if row_flag != is_json_x402:
                    continue
            if query_lower is not None:
                haystack = " ".join(
                    row.get(col, "")
                    for col in ("url", "operator", "asset", "notes", "discovered_via")
                ).lower()
                if query_lower not in haystack:
                    continue
            matched.append(row)

        page = matched[offset : offset + limit]
        return {
            "dataset": DATASET_FILES["endpoints"],
            "total_rows": len(rows),
            "matched_rows": len(matched),
            "returned_rows": len(page),
            "limit": limit,
            "offset": offset,
            "columns": headers,
            "summary": {
                "networks": _count_by_key(matched, "network"),
                "price_bands": _count_by_key(matched, "price_band"),
                "verified_statuses": _count_by_key(matched, "verified"),
            },
            "rows": [_format_endpoint_row(row) for row in page],
        }

    def _list_guardrails_benchmark(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit, offset = _clamp_pagination(args)
        benchmark_domain = _parse_optional_str(args, "benchmark_domain")
        metric_key = _parse_optional_str(args, "metric_key")
        query = _parse_optional_str(args, "query")

        path = _resolve_dataset_file(self.dataset_root, "guardrails")
        _, headers, rows, _ = _read_csv_snapshot(path)

        matched: List[Dict[str, str]] = []
        metric_lower = metric_key.lower() if metric_key is not None else None
        query_lower = query.lower() if query is not None else None
        for row in rows:
            if (
                benchmark_domain is not None
                and row.get("benchmark_domain", "").strip().lower() != benchmark_domain.lower()
            ):
                continue
            if metric_lower is not None and metric_lower not in row.get("metric_key", "").lower():
                continue
            if query_lower is not None:
                haystack = " ".join(
                    row.get(col, "")
                    for col in ("benchmark_domain", "metric_key", "source_file")
                ).lower()
                if query_lower not in haystack:
                    continue
            matched.append(row)

        page = matched[offset : offset + limit]
        domains = sorted({row.get("benchmark_domain", "") for row in matched if row.get("benchmark_domain")})
        return {
            "dataset": DATASET_FILES["guardrails"],
            "total_rows": len(rows),
            "matched_rows": len(matched),
            "returned_rows": len(page),
            "limit": limit,
            "offset": offset,
            "columns": headers,
            "domains": domains,
            "rows": page,
        }

    def _list_apify_kits_catalog(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit, offset = _clamp_pagination(args)
        channel = _parse_optional_str(args, "channel")
        billing_model = _parse_optional_str(args, "billing_model")
        in_manifest_only = _parse_bool_arg(args.get("in_manifest_only"), "in_manifest_only")
        slug = _parse_optional_str(args, "slug")
        query = _parse_optional_str(args, "query")
        raw_max_price = args.get("max_price_usd")
        max_price_usd: Optional[Decimal] = None
        if raw_max_price is not None:
            max_price_usd = _parse_decimal(raw_max_price, "max_price_usd")
            if max_price_usd < Decimal("0"):
                raise ValueError("Argument 'max_price_usd' must be non-negative")

        path = _resolve_dataset_file(self.dataset_root, "catalog")
        _, headers, rows, _ = _read_csv_snapshot(path)

        matched: List[Dict[str, str]] = []
        slug_lower = slug.lower() if slug is not None else None
        query_lower = query.lower() if query is not None else None
        total_price_usd = Decimal("0.00")
        total_atomic_usdc = 0

        with localcontext() as ctx:
            ctx.prec = 38
            for row in rows:
                if channel is not None and row.get("channel", "").strip().lower() != channel.lower():
                    continue
                if (
                    billing_model is not None
                    and row.get("billing_model", "").strip().lower() != billing_model.lower()
                ):
                    continue
                if in_manifest_only is not None:
                    row_manifest = row.get("in_gumroad_13_pack_manifest", "").strip().lower() == "true"
                    if row_manifest != in_manifest_only:
                        continue
                if slug_lower is not None and slug_lower not in row.get("slug", "").lower():
                    continue
                row_price = _parse_decimal(
                    row.get("recommended_price_usd", "0") or "0",
                    "recommended_price_usd",
                )
                if max_price_usd is not None and row_price > max_price_usd:
                    continue
                if query_lower is not None:
                    haystack = " ".join(
                        row.get(col, "")
                        for col in ("slug", "title", "channel", "relative_dist_path")
                    ).lower()
                    if query_lower not in haystack:
                        continue
                matched.append(row)
                total_price_usd += row_price
                raw_atomic = row.get("price_atomic_usdc_6dec", "0").strip()
                if raw_atomic.isdigit():
                    total_atomic_usdc += int(raw_atomic)

            formatted_total = str(total_price_usd.quantize(Decimal("0.01")))

        page = matched[offset : offset + limit]
        return {
            "dataset": DATASET_FILES["catalog"],
            "total_rows": len(rows),
            "matched_rows": len(matched),
            "returned_rows": len(page),
            "limit": limit,
            "offset": offset,
            "columns": headers,
            "matched_total_price_usd": formatted_total,
            "matched_total_atomic_usdc_6dec": total_atomic_usdc,
            "rows": [_format_catalog_row(row) for row in page],
        }

    def _verify_dataset_integrity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        dataset_arg = _parse_optional_str(args, "dataset") or "all"
        include_headers_opt = _parse_bool_arg(args.get("include_headers"), "include_headers")
        include_headers = True if include_headers_opt is None else include_headers_opt

        if dataset_arg == "all":
            keys = list(DATASET_FILES.keys())
        elif dataset_arg in DATASET_FILES:
            keys = [dataset_arg]
        else:
            raise ValueError(
                f"Argument 'dataset' must be one of ['all', 'endpoints', 'guardrails', 'catalog'], got {dataset_arg!r}"
            )

        records: List[Dict[str, Any]] = []
        all_present = True
        all_rectangular = True

        for key in keys:
            path = _resolve_dataset_file(self.dataset_root, key)
            raw_bytes, headers, rows, rectangular = _read_csv_snapshot(path)
            sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
            exists = path.is_file()
            all_present = all_present and exists
            all_rectangular = all_rectangular and rectangular
            entry: Dict[str, Any] = {
                "key": key,
                "filename": DATASET_FILES[key],
                "exists": exists,
                "byte_size": len(raw_bytes),
                "sha256": sha256_hex,
                "row_count": len(rows),
                "column_count": len(headers),
                "rectangular": rectangular,
            }
            if include_headers:
                entry["headers"] = headers
            records.append(entry)

        ok = (
            all_present
            and all_rectangular
            and all(item["row_count"] > 0 for item in records)
        )
        return {
            "ok": ok,
            "datasets_checked": len(records),
            "all_present": all_present,
            "all_rows_rectangular": all_rectangular,
            "datasets": records,
        }

    def serve_stdio(
        self,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
    ) -> None:
        in_stream = stdin if stdin is not None else sys.stdin
        out_stream = stdout if stdout is not None else sys.stdout
        for raw_line in in_stream:
            line = raw_line.strip()
            if not line:
                continue
            try:
                msg = _parse_json_line(line)
            except (json.JSONDecodeError, ValueError):
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                out_stream.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
                out_stream.flush()
                continue
            resp = self.handle_request(msg)
            if resp is not None:
                out_stream.write(json.dumps(resp, ensure_ascii=False) + "\n")
                out_stream.flush()


def run_self_test(dataset_dir: Optional[Union[Path, str]] = None) -> Dict[str, Any]:
    """Run an offline MCP stdio self-test exercising initialize, tools/list, and all 4 tools."""
    server = AgenticX402MCPServer(dataset_dir=dataset_dir)
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "x402_list_endpoints_benchmark", "arguments": {"limit": 5}},
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "x402_list_guardrails_benchmark", "arguments": {"limit": 5}},
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "x402_list_apify_kits_catalog", "arguments": {"limit": 5}},
        },
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "x402_verify_dataset_integrity", "arguments": {}},
        },
    ]
    in_buf = io.StringIO("\n".join(json.dumps(req) for req in requests) + "\n")
    out_buf = io.StringIO()
    server.serve_stdio(stdin=in_buf, stdout=out_buf)

    responses = [json.loads(line) for line in out_buf.getvalue().splitlines() if line.strip()]
    tools = responses[1]["result"]["tools"]
    integrity = json.loads(responses[5]["result"]["content"][0]["text"])
    ok = (
        len(responses) == 6
        and responses[0]["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
        and len(tools) == 4
        and all(not resp["result"]["isError"] for resp in responses[2:])
        and bool(integrity.get("ok"))
    )
    return {
        "ok": ok,
        "server_version": __version__,
        "protocol_version": MCP_PROTOCOL_VERSION,
        "tools_count": len(tools),
        "tool_names": [t["name"] for t in tools],
        "integrity": integrity,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentic-x402-mcp",
        description=(
            "Zero-dependency MCP stdio JSON-RPC 2.0 server for 2026 x402 micro-payment "
            "benchmarks, dev tooling guardrails, and Apify kit catalogs."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"agentic-x402-apify-kits {__version__}",
    )
    parser.add_argument(
        "--dataset-dir",
        default=None,
        help="Optional directory path containing the 3 benchmark CSV datasets.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Verify dataset integrity and exercise initialize, tools/list, and all 4 MCP tools.",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run JSON-RPC 2.0 MCP server over stdin/stdout (default behavior).",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        report = run_self_test(dataset_dir=args.dataset_dir)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1

    server = AgenticX402MCPServer(dataset_dir=args.dataset_dir)
    server.serve_stdio()
    return 0


if __name__ == "__main__":
    sys.exit(main())
