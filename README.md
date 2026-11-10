# Agentic `x402` Micro-Payment Boilerplates, Apify Pay-Per-Event (`PPE`) Actors & Empirical Benchmarks (2026)

[![Live Storefront](https://img.shields.io/badge/Live_Storefront-GitHub_Pages-10B981?style=for-the-badge&logo=github)](https://tunguyen1993.github.io/agentic-x402-apify-kits-2026/)
[![Release v2026.11.0](https://img.shields.io/badge/Apify_PPE_Actor_ZIPs-Release_v2026.11.0-38BDF8?style=for-the-badge&logo=github)](https://github.com/tunguyen1993/agentic-x402-apify-kits-2026/releases/tag/v2026.11.0)
[![NexusAI Token Store](https://img.shields.io/badge/NexusAI_Token_Store-OpenAI_&_Anthropic_Gateway-8B5CF6?style=for-the-badge)](https://booking-passed-pencil-sticker.trycloudflare.com/store)

> **Live Interactive Catalog & Benchmark Storefront:**  
> **https://tunguyen1993.github.io/agentic-x402-apify-kits-2026/**
>
> **NexusAI Multi-Pool LLM Token Store (`99,000 VND – 1,490,000 VND` · OpenAI & Anthropic Compatible):**  
> **https://booking-passed-pencil-sticker.trycloudflare.com/store**
>
> **Dataset Schema:** `2026.11.track5.v1.1` (`100%` deterministic empirical telemetry, fixed-point `Decimal` atomic math, `88` unified AST/regex pre-commit guardrails).

---

## 1. Apify Store Pay-Per-Event (`PPE`) Actor Releases (`v2026.11.0`)

Both Actors target `apify/actor-python:3.12`, implement native `Actor.charge()` Pay-Per-Event metering with automatic `event_charge_limit_reached` spending-cap protection, include standalone offline/live CLI modes, and ship as reproducible SHA-256 verified `.zip` archives on **[GitHub Release `v2026.11.0`](https://github.com/tunguyen1993/agentic-x402-apify-kits-2026/releases/tag/v2026.11.0)**:

| # | Actor Slug | Direct Release `.zip` Download | PPE Events | Files | ZIP Bytes | SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `ai-agent-clean-markdown-x402-extractor` | [**`01_apify_ppe_x402_markdown_extractor.zip`**](https://github.com/tunguyen1993/agentic-x402-apify-kits-2026/releases/download/v2026.11.0/01_apify_ppe_x402_markdown_extractor.zip) | `actor-start` (`$0.005`), `page-extracted` (`$0.002`) | 10 | `25,664` | `7f429e6da8236d2195482173a8776ddf3ef786b884b4d858d96f68b665b95671` |
| 2 | `web3-oss-zero-bond-bounty-radar` | [**`02_apify_ppe_zero_bond_bounty_radar.zip`**](https://github.com/tunguyen1993/agentic-x402-apify-kits-2026/releases/download/v2026.11.0/02_apify_ppe_zero_bond_bounty_radar.zip) | `bounty-enriched` (`$0.003`) | 10 | `21,987` | `863c36c7733406abad54cf287ef815bc73f8acdbfdf2e2d9ef4e11ac52b0cfb5` |

### Actor Capabilities
- **Actor #1 (`ai-agent-clean-markdown-x402-extractor`):** Polite `robots.txt`-compliant HTML -> clean LLM Markdown + `JSON-LD` structured entity extraction + automatic `llms.txt` synthesis + passive zero-spend `HTTP 402` (`PAYMENT-REQUIRED` / `/.well-known/x402`) discovery with SSRF & cross-origin redirect credential stripping.
- **Actor #2 (`web3-oss-zero-bond-bounty-radar`):** Cross-platform `$0`-bond cash bounty normalization, canonical GitHub issue deduplication, Bidi/honeypot screening, and fixed-point Expected Value ranking (`Decimal(Reward_USD) / Decimal(1 + OpenPRs)`) across **Superteam Earn**, **Algora**, **Polar.sh**, **Opire**, and **IssueHunt**.

---

## 2. Empirical 2026 `x402` Census & Guardrail Benchmarks (Included CSV Datasets)

All raw CSV tables are committed directly in this repository for reproducible analysis:

- [**`x402_endpoints_benchmark_2026.csv`**](./x402_endpoints_benchmark_2026.csv) — `51` deduplicated `x402` endpoints (`18` Base `eip155:8453`, `32` BNB Chain `eip155:56`, plus `1` stateless loopback reference pod) sampled from **`33,064` CDP Bazaar indexed resources**.
- [**`dev_tooling_guardrails_benchmark_2026.csv`**](./dev_tooling_guardrails_benchmark_2026.csv) — `20` empirical benchmark metrics across `x402` pricing bands, `52` production code-mistake rules (`11 CRITICAL`, `31 HIGH`, `10 MEDIUM`), `19` active zero-fee Web3 bug bounty programs, and Apple Silicon CLI compatibility.
- [**`gumroad_bundles_catalog_2026.csv`**](./gumroad_bundles_catalog_2026.csv) — Exact file counts, compressed/uncompressed byte sizes, `6`-decimal atomic USDC prices, and SHA-256 digests across all `13` flagship kits + `3` supplementary archives.

| Benchmark Metric | Verified Value | Key Takeaway |
| :--- | :--- | :--- |
| **CDP Bazaar Indexed Resources** | `33,064` | Machine-payable `HTTP 402` endpoints have reached production scale |
| **Sampled Endpoint Rail Split** | `18` Base / `32` BSC (+ `1` pod) | 6-decimal Base `USDC` (`0x8335...2913`) & 18-decimal BSC `USD1` (`0x8d0d...8b0d`) |
| **Sub-Cent Pricing (`< $0.01`)** | `25` endpoints (`50%`) | Clean Markdown extraction & lightweight agent queries cluster at `$0.001–$0.005` |
| **Cent-Scale Pricing (`$0.01–$0.10`)** | `20` endpoints (`40%`) | Multi-step forensics, anomaly scans, and enriched feeds |
| **Reference `402` Overhead** | `3 ms` `/health` · `1 ms` `402` | Stateless receive-only `HTTP 402` descriptors add ~`1 ms` latency |
| **Automated Pre-Commit Guardrails** | `88` rules (`52 CM` + `36 Rust`) | Prevents IEEE-754 float drift, SSRF redirects, mass assignment & Trojan Bidi chars |

---

## 3. Complete 13-Pack Standalone Engineering Catalog (`$19–$59` · `$482.00` Total Value)

Total compressed size across the 13-pack developer catalog: **`856,303` bytes** (`2,856,619` bytes uncompressed; `482,000,000` atomic 6-decimal USDC equivalent):

| # | Slug | Product Title | Price (USD) | Files | ZIP Bytes | SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `x402-api-boilerplate` | x402 API Micro-SaaS Boilerplate: Pay-Per-Request APIs for AI Agents | `$29.00` | 5 | `64,023` | `cc0534284688583d858c73795c7311aba25bb5030cae4afc625a93c778fbfb51` |
| 2 | `ai-coding-agent-eval-and-swe-harness-2026` | SWE Eval Harness & Adversarial Multi-Model Council | `$49.00` | 4 | `35,076` | `613197deae50a92f37bc0933632099c8efb24038c1de1a28e361afa5d144802b` |
| 3 | `ai-engineering-prompts` | 500 Production AI Engineering System Prompts + 5-Layer Visual Director Bible | `$19.00` | 6 | `159,001` | `22327894b56a47bfe42f776e1bcc3b17410e07d49a1c24b58d3e674de0d0c5be` |
| 4 | `mcp-server-kit` | Production MCP & Autonomous Agent Server Kit (8-File Suite) | `$29.00` | 8 | `171,518` | `8fbba300fdc878f11eef4401ea4dd789b9b16187082af8dd2a340750fa51e51c` |
| 5 | `nextjs15-fastapi-stripe-saas-starter-2026` | Next.js 15 + FastAPI + RBAC + Stripe SaaS Starter | `$49.00` | 4 | `41,475` | `78f226642f8b6111c8bc20d5ddaff0a6c9c6963d56073664ae266391205aaf92` |
| 6 | `python-async-playwright-stealth-data-pipelines-2026` | Compliant Async HTTP/ETL & Citation Auditor Pipeline | `$39.00` | 4 | `51,659` | `53dc4dd69bb1d1bc72bf1a878ef58c376a6c21857afcb3600ce4dfd005674359` |
| 7 | `quant-crypto-microstructure-backtester-2026` | Quantitative Crypto Funding-Rate & Microstructure Backtesting Suite | `$39.00` | 7 | `108,588` | `cb3f2183011374d1ed125bd5c0d49628638d7e6543e6cd1bed286134c6fbfb3b` |
| 8 | `rust-tokio-high-frequency-networking-templates-2026` | Low-Latency Rust Tokio Orderbook Sync Manual & Engine | `$59.00` | 3 | `30,415` | `11601d50d5fe329c12aa2f35a97a1c889a5e9fcb0a4c13171d0bd9e00ca8f728` |
| 9 | `solana-anchor-rust-security-and-mev-kit-2026` | Solana Anchor Smart Contract Security & Forensics Handbook (2026) | `$59.00` | 5 | `53,726` | `f22c0f8ec9275ff5217aa8f87bf51a5e50bcbb0db39d9dcdc22b646975ffe9ba` |
| 10 | `solidity-foundry-audit-suite-2026` | DeFi & Solidity Smart Contract Security Audit Bible + Foundry PoC Templates | `$39.00` | 8 | `127,458` | `e34311a425d721ae8439d71e53a8cc96853e70a8c6c77b17f45be6bdf90cbd54` |
| 11 | `01-mcp-token-saver-kit-gumroad-bundle` | MCP Smart Codebase & AST Token Saver (`62%–68%` Context Reduction) | `$19.00` | 4 | `7,678` | `718c587ed831a66903a4e726b195b7cd005ede50d042b1f57f5ca831191cd08c` |
| 12 | `02-ai-security-reverse-eng-audit-kit-gumroad-bundle` | AI Agent & MCP Security Secret-Leak Auditor CLI | `$29.00` | 2 | `3,337` | `b93de2f0e31cc4b23633e34d5015665f1f75c6df8cdd3fd5d1655bf0606b730d` |
| 13 | `03-github-bounty-autopilot-kit-gumroad-bundle` | GitHub Cash Bounty Radar & Anti-Honeypot CLI | `$24.00` | 2 | `2,349` | `c347cbf107fe46d6f16f16872a74567cdb9fc54785490960665f28cce7c93f39` |

---

## 4. High-Throughput Multi-Pool Inference: NexusAI Token Store

Running multi-agent SWE harnesses, Cursor, Claude Code, and MCP toolchains demands high-RPM frontier routing without TOCTOU quota race conditions. Our **NexusAI Orbital Gateway** provides drop-in OpenAI (`/v1/chat/completions`) and Anthropic (`/v1/messages`) compatibility with atomic in-flight token reservation and `crypto.timingSafeEqual` key isolation:

| Plan | Token Quota (30 Days) | Rate Limit | Price |
| :--- | :--- | :--- | :--- |
| **Starter** | `10,000,000` Tokens | `60 RPM` | **`99,000 VND`** |
| **Pro Coder** | `50,000,000` Tokens | `120 RPM` | **`299,000 VND`** |
| **VIP Agency** | `200,000,000` Tokens | `300 RPM` | **`799,000 VND`** |
| **Unlimited Pro** | Fair-Use Unlimited | `300 RPM` | **`1,490,000 VND`** |

Explore live tiers & instant IDE integration docs:  
**https://booking-passed-pencil-sticker.trycloudflare.com/store**

---

## 5. Verify Release Checksums

```bash
curl -sLO https://github.com/tunguyen1993/agentic-x402-apify-kits-2026/releases/download/v2026.11.0/01_apify_ppe_x402_markdown_extractor.zip
curl -sLO https://github.com/tunguyen1993/agentic-x402-apify-kits-2026/releases/download/v2026.11.0/02_apify_ppe_zero_bond_bounty_radar.zip
shasum -a 256 01_apify_ppe_x402_markdown_extractor.zip 02_apify_ppe_zero_bond_bounty_radar.zip
```
