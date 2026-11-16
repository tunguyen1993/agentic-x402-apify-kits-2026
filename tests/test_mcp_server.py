"""Unit tests for the zero-dependency Agentic x402 & Apify Kits MCP server."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from agentic_x402_mcp import (
    DATASET_FILES,
    MCP_PROTOCOL_VERSION,
    AgenticX402MCPServer,
    __version__,
    main,
    resolve_dataset_root,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_SHA256 = {
    "endpoints": "4df92c55100fabbba86c3f74bc0157d174c75a05fb9160c5268b79f99d362caa",
    "guardrails": "e5e97350fbe49dfe736bf0523b1d1db50ea1d460c81c7aaa1c37dcfb291d37a3",
    "catalog": "e39df65179550a537422e1fc96935cc223a3dbb6ae58222658a44758703fae6b",
}


class TestAgenticX402MCPServer(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AgenticX402MCPServer(dataset_dir=REPO_ROOT)

    def test_initialize_and_notifications_initialized_stdio_roundtrip(self) -> None:
        stream_in = "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps({"jsonrpc": "2.0", "id": 0, "method": "ping"}),
            ]
        )
        out_buf = io.StringIO()
        self.server.serve_stdio(stdin=io.StringIO(stream_in + "\n"), stdout=out_buf)
        responses = [json.loads(line) for line in out_buf.getvalue().splitlines() if line.strip()]

        self.assertEqual(len(responses), 2)
        init_resp, ping_resp = responses
        self.assertEqual(init_resp["id"], 1)
        self.assertEqual(init_resp["result"]["protocolVersion"], MCP_PROTOCOL_VERSION)
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "agentic-x402-apify-kits")
        self.assertEqual(init_resp["result"]["serverInfo"]["version"], __version__)
        self.assertIn("tools", init_resp["result"]["capabilities"])
        self.assertEqual(ping_resp["id"], 0)
        self.assertEqual(ping_resp["result"], {})

    def test_tools_list_and_explicit_boolean_annotations(self) -> None:
        resp = self.server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertIsNotNone(resp)
        assert resp is not None
        tools = resp["result"]["tools"]
        self.assertEqual(len(tools), 4)

        expected_names = {
            "x402_list_endpoints_benchmark",
            "x402_list_guardrails_benchmark",
            "x402_list_apify_kits_catalog",
            "x402_verify_dataset_integrity",
        }
        self.assertEqual({t["name"] for t in tools}, expected_names)

        for tool in tools:
            self.assertIn("annotations", tool)
            ann = tool["annotations"]
            self.assertIsInstance(ann.get("title"), str)
            self.assertTrue(len(ann["title"]) > 0)
            for key in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
                self.assertIn(key, ann)
                self.assertIsInstance(ann[key], bool)
            self.assertIs(ann["readOnlyHint"], True)
            self.assertIs(ann["destructiveHint"], False)
            self.assertIs(ann["idempotentHint"], True)
            self.assertIs(ann["openWorldHint"], False)

    def test_tool_call_endpoints_benchmark_and_filters(self) -> None:
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_endpoints_benchmark",
                    "arguments": {
                        "network": "eip155:8453",
                        "verified": "handshake",
                        "price_band": "<$0.01",
                        "is_json_x402": True,
                        "limit": 10,
                    },
                },
            }
        )
        assert resp is not None
        self.assertFalse(resp["result"]["isError"])
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["dataset"], "x402_endpoints_benchmark_2026.csv")
        self.assertEqual(payload["total_rows"], 51)
        self.assertEqual(payload["matched_rows"], 3)
        self.assertEqual(payload["returned_rows"], 3)
        for row in payload["rows"]:
            self.assertEqual(row["network"], "eip155:8453")
            self.assertEqual(row["verified"], "handshake")
            self.assertEqual(row["price_band"], "<$0.01")
            self.assertIs(row["is_json_x402"], True)

    def test_tool_call_guardrails_benchmark_and_filters(self) -> None:
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_guardrails_benchmark",
                    "arguments": {
                        "benchmark_domain": "code_mistakes_guard",
                        "metric_key": "critical",
                    },
                },
            }
        )
        assert resp is not None
        self.assertFalse(resp["result"]["isError"])
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["dataset"], "dev_tooling_guardrails_benchmark_2026.csv")
        self.assertEqual(payload["total_rows"], 20)
        self.assertEqual(payload["matched_rows"], 1)
        self.assertEqual(payload["rows"][0]["metric_key"], "critical_severity_rules")
        self.assertEqual(payload["rows"][0]["empirical_value"], "11")

    def test_tool_call_apify_kits_catalog_and_decimal_filter(self) -> None:
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_apify_kits_catalog",
                    "arguments": {
                        "in_manifest_only": True,
                        "max_price_usd": 29,
                        "limit": 20,
                    },
                },
            }
        )
        assert resp is not None
        self.assertFalse(resp["result"]["isError"])
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["dataset"], "gumroad_bundles_catalog_2026.csv")
        self.assertEqual(payload["total_rows"], 16)
        self.assertGreater(payload["matched_rows"], 0)
        self.assertEqual(payload["matched_rows"], 6)
        self.assertEqual(payload["matched_total_price_usd"], "149.00")
        self.assertEqual(payload["matched_total_atomic_usdc_6dec"], 149000000)
        for row in payload["rows"]:
            self.assertIs(row["in_gumroad_13_pack_manifest"], True)
            self.assertLessEqual(row["price_atomic_usdc_6dec"], 29000000)

    def test_tool_call_verify_dataset_integrity_and_package_data_parity(self) -> None:
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "x402_verify_dataset_integrity",
                    "arguments": {"include_headers": True},
                },
            }
        )
        assert resp is not None
        self.assertFalse(resp["result"]["isError"])
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["datasets_checked"], 3)
        self.assertTrue(payload["all_present"])
        self.assertTrue(payload["all_rows_rectangular"])

        by_key = {item["key"]: item for item in payload["datasets"]}
        self.assertEqual(by_key["endpoints"]["row_count"], 51)
        self.assertEqual(by_key["endpoints"]["column_count"], 11)
        self.assertEqual(by_key["endpoints"]["sha256"], EXPECTED_SHA256["endpoints"])
        self.assertEqual(by_key["guardrails"]["row_count"], 20)
        self.assertEqual(by_key["guardrails"]["column_count"], 5)
        self.assertEqual(by_key["guardrails"]["sha256"], EXPECTED_SHA256["guardrails"])
        self.assertEqual(by_key["catalog"]["row_count"], 16)
        self.assertEqual(by_key["catalog"]["column_count"], 14)
        self.assertEqual(by_key["catalog"]["sha256"], EXPECTED_SHA256["catalog"])

        pkg_data_dir = REPO_ROOT / "src" / "agentic_x402_mcp" / "data"
        for key, filename in DATASET_FILES.items():
            pkg_hash = hashlib.sha256((pkg_data_dir / filename).read_bytes()).hexdigest()
            self.assertEqual(pkg_hash, EXPECTED_SHA256[key])

    def test_limit_clamping_and_validation_edge_cases(self) -> None:
        high_resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_endpoints_benchmark",
                    "arguments": {"limit": 999, "offset": -5},
                },
            }
        )
        assert high_resp is not None
        high_payload = json.loads(high_resp["result"]["content"][0]["text"])
        self.assertEqual(high_payload["limit"], 100)
        self.assertEqual(high_payload["offset"], 0)
        self.assertEqual(high_payload["returned_rows"], 51)

        low_resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_endpoints_benchmark",
                    "arguments": {"limit": 0, "offset": 50},
                },
            }
        )
        assert low_resp is not None
        low_payload = json.loads(low_resp["result"]["content"][0]["text"])
        self.assertEqual(low_payload["limit"], 1)
        self.assertEqual(low_payload["offset"], 50)
        self.assertEqual(low_payload["returned_rows"], 1)

        bool_limit_resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_endpoints_benchmark",
                    "arguments": {"limit": True},
                },
            }
        )
        assert bool_limit_resp is not None
        self.assertTrue(bool_limit_resp["result"]["isError"])

    def test_unknown_tool_and_malformed_jsonrpc_errors(self) -> None:
        unknown_tool_resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {"name": "unknown_tool_xyz", "arguments": {}},
            }
        )
        assert unknown_tool_resp is not None
        self.assertTrue(unknown_tool_resp["result"]["isError"])
        self.assertIn("Unknown MCP tool", unknown_tool_resp["result"]["content"][0]["text"])

        unknown_method_resp = self.server.handle_request(
            {"jsonrpc": "2.0", "id": 31, "method": "resources/nonexistent"}
        )
        assert unknown_method_resp is not None
        self.assertEqual(unknown_method_resp["error"]["code"], -32601)

        unknown_arg_resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 32,
                "method": "tools/call",
                "params": {
                    "name": "x402_list_endpoints_benchmark",
                    "arguments": {"unexpected_param": "abc"},
                },
            }
        )
        assert unknown_arg_resp is not None
        self.assertTrue(unknown_arg_resp["result"]["isError"])
        self.assertIn("Unsupported argument", unknown_arg_resp["result"]["content"][0]["text"])

        bad_stream = io.StringIO(
            "\n".join(
                [
                    "{not valid json",
                    "[1, 2, 3]",
                    "{}",
                    json.dumps({"jsonrpc": "1.0", "id": 33, "method": "ping"}),
                    json.dumps({"jsonrpc": "2.0", "id": True, "method": "ping"}),
                    '{"jsonrpc":"2.0","id":34,"method":"tools/call","params":{"name":"x402_list_apify_kits_catalog","arguments":{"max_price_usd":NaN}}}',
                ]
            )
            + "\n"
        )
        out_buf = io.StringIO()
        self.server.serve_stdio(stdin=bad_stream, stdout=out_buf)
        err_resps = [json.loads(line) for line in out_buf.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(err_resps), 6)
        self.assertEqual(err_resps[0]["error"]["code"], -32700)
        self.assertEqual(err_resps[1]["error"]["code"], -32600)
        self.assertEqual(err_resps[2]["error"]["code"], -32600)
        self.assertEqual(err_resps[3]["error"]["code"], -32600)
        self.assertEqual(err_resps[4]["error"]["code"], -32600)
        self.assertEqual(err_resps[5]["error"]["code"], -32700)

        # Ensure server keeps processing valid requests cleanly after errors
        recovery_resp = self.server.handle_request({"jsonrpc": "2.0", "id": 35, "method": "ping"})
        assert recovery_resp is not None
        self.assertEqual(recovery_resp["result"], {})

    def test_symlink_and_missing_dataset_dir_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                resolve_dataset_root(tmp_path)

            outside_file = tmp_path / "outside.csv"
            outside_file.write_text("col1\nval1\n", encoding="utf-8")
            ds_dir = tmp_path / "ds"
            ds_dir.mkdir()
            (ds_dir / DATASET_FILES["endpoints"]).symlink_to(outside_file)
            (ds_dir / DATASET_FILES["guardrails"]).write_text("a\n1\n", encoding="utf-8")
            (ds_dir / DATASET_FILES["catalog"]).write_text("a\n1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                resolve_dataset_root(ds_dir)

    def test_cli_self_test_and_help(self) -> None:
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            rc = main(["--self-test"])
        self.assertEqual(rc, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertTrue(report["ok"])
        self.assertEqual(report["tools_count"], 4)

        help_buf = io.StringIO()
        with self.assertRaises(SystemExit) as cm:
            with contextlib.redirect_stdout(help_buf):
                main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("agentic-x402-mcp", help_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
