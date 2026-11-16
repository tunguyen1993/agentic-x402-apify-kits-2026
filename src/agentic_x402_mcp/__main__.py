"""Module entrypoint for `python -m agentic_x402_mcp`."""

from __future__ import annotations

import sys

from agentic_x402_mcp.mcp_server import main

if __name__ == "__main__":
    sys.exit(main())
