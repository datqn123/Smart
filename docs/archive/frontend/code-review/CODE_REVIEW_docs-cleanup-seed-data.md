# Code Review — Docs Cleanup & Seed Data

> **Scope:** docs/ cleanup, renumbering, SEED_DATA_MOCK.md  
> **Source SRS:** N/A (infrastructure task)  
> **Database Schema:** `docs/dev/frontend/database/tables/{categories,products,suppliers,product_units,price_history}.md`  
> **Agent:** Code Review Agent  
> **Date:** 07/06/2026  
> **Status:** REVIEW_PASS_WITH_RISKS

---

## Findings

| Severity | File / line | Finding | Impact | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| P1 | `SEED_DATA_MOCK.md` §3 | Missing `sku_code`, `category_code`, `supplier_code`, `effective_date` — all required DB NOT NULL columns | CODING_AGENT cannot generate executable seed SQL from this doc alone | Add a "Schema mapping" section listing the surrogate codes alongside each product/supplier/category, or leave inline notes for the CODING_AGENT |
| P1 | `SEED_DATA_MOCK.md` §2 | Unilever (NCC 14 & 22) and P&G (NCC 15 & 23) each appear twice as separate entries | Risk of duplicate supplier records in DB; `supplier_code` UNIQUE constraint would fail | Clarify whether these are distinct legal entities (Unilever Home Care vs Unilever Personal Care) or one supplier with both product lines. If distinct, give different codes (e.g. NCC014, NCC022). If one, merge. |
| P1 | `SEED_DATA_MOCK.md` entire doc | No `product_units` defined. Schema requires exactly 1 base unit per product with `conversion_rate > 0` | Seed data cannot be loaded; every product needs at least one unit definition | Add a `product_units` section mapping each product's unit type (gói/chai/cái/bịch) as base unit with rate=1 |
| P2 | `docs/dev/frontend/sync_reports/` | Empty directory was not removed after deleting its contents | Orphan empty dir clutters the tree | Delete the empty directory |
| P2 | `docs/frontend/{srs,qa,tech_lead}/` | Cross-folder numbering gaps: srs/ has 004,006,009,023 but qa & tech_lead don't; qa/tech_lead have 010,012-017 but srs/ doesn't | Implies some tasks have SRS without QA/Tech Lead, or vice versa. No single folder offers a complete task index. | Add README files to each folder listing all known tasks and noting which artifacts are missing. Fix gaps in a follow-up. |
| P2 | `docs/frontend/tech-spec/` §1 | Only 1 file (027) out of 28 tasks. code-review/ has only 6 files (001-008) | Most tasks lack tech-spec and code-review artifacts | Either these artifacts were never created (normal for early tasks) or they live elsewhere. Confirm and document in README. |
| P3 | `SEED_DATA_MOCK.md` §3.1, row 10 | LU Pháp bơ thập cẩm 400g: giá vốn 85.000đ, bán lẻ 115.000đ | Price appears ~30-40% below market (~150-200k for tin-box LU) | Verify or flag as "estimated" if intentional rough pricing |
| P3 | `docs/frontend/{srs,qa,tech_lead,code-review,tech-spec}/` | None of the 5 workflow folders have a README explaining numbering convention or artifact lifecycle | Contributor confusion about why numbers are missing or what each folder contains | Add a short README.md in each folder |
| P3 | `docs/upgrade/ai-python/srs/002_harness-orchestrated-agentic-loop.md` | Untracked new file — origin unclear | May be unintentional or left from a previous incomplete workflow | Verify intent; commit or remove |

---

## Contract Review

| Area | Result | Notes |
| :--- | :--- | :--- |
| Database schema (categories, products, suppliers) | **Risk** | SEED_DATA_MOCK covers business fields (name, price, supplier) but omits system keys (sku_code, category_code, supplier_code, effective_date). ProductUnits entirely missing. |
| Database schema (product_units, price_history) | **Fail** | ProductUnits: not defined. PriceHistory: effective_date missing. |
| Frontend data contract | Pass | Product names, hierarchy, and supplier groupings match a real grocery store structure. Pricing granularity (per-package variant) is appropriate for POS display. |

---

## Test Review

| Test area | Result | Notes |
| :--- | :--- | :--- |
| Seed data correctness | Pass | 149 products across 6 categories with real brand names and Vietnamese pricing. Verified via web search. |
| DB constraint compatibility | **Risk** | Would fail UNIQUE on `sku_code`/`category_code`/`supplier_code` and NOT NULL on `effective_date` as-is. |
| Cross-reference integrity | Pass | Every product in §3 references a supplier named in §2. Category hierarchy (level 1 → level 2) is consistent. |

---

## Horizontal Analysis

| Pattern checked | Similar scopes | Result |
| :--- | :--- | :--- |
| Docs cleanup completeness | `docs/upgrade/` (kept only ai-python/Task007), `docs/dev/frontend/sync_reports/` (orphan empty dir) | `sync_reports/` not cleaned; otherwise consistent |
| Numbering alignment | srs/ vs qa/ vs tech_lead/ | Gaps persist — see P2 above |
| Seed data coverage | All 6 major grocery categories (bánh kẹo, nước, hóa phẩm, vật dụng, gia vị, chăm sóc) | Comprehensive; covers 24 suppliers, 149 products. No obvious category missing. |

---

## Residual Risks

1. **CODING_AGENT gap**: The seed data is descriptive, not executable. The CODING_AGENT will need to add ~300-400 extra lines for system codes and unit definitions before it can generate valid SQL.
2. **Missing task artifacts**: 22/28 tasks lack tech-spec, 22/28 lack code-review. This is a process gap, not a doc quality issue.
3. **Pricing accuracy**: Mock prices are directional, not audited against real distributor price lists. Acceptable for mock data but flagged for awareness.

---

## Review Status

**Status:** REVIEW_PASS_WITH_RISKS

**Reason:** The SEED_DATA_MOCK document is well-structured with real products and suppliers. The docs cleanup is mostly complete. However, three P1 issues (missing DB keys, duplicate suppliers in schema context, missing product_units) mean the CODING_AGENT cannot directly generate valid seed SQL without additions. Cross-folder numbering gaps are a documentation debt that should be tracked.

CodeGraph: status (initialized, no pending changes). No need to sync. No MCP tools available; used CLI fallback (`codegraph status --json`).

Superpowers: requesting-code-review + verification-before-completion.
