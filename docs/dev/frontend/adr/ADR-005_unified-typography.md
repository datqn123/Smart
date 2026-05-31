# ADR-005: Unified Typography System

**Status: Proposed**
**Date: 2026-04-20**

## Context
The application currently has inconsistent typography across different modules. Tables use varying font weights for headers, and Forms use small, uppercase labels that are difficult to read and inconsistent with modern UI trends.

## Decision
We will centralize all common Typography classes in `src/lib/data-table-layout.ts` to enforce consistency.

## Tokens
- `TABLE_HEAD_CLASS`: `text-[12px] font-bold uppercase tracking-wider text-slate-500`
- `TABLE_CELL_PRIMARY_CLASS`: `text-sm font-semibold text-slate-900`
- `TABLE_CELL_SECONDARY_CLASS`: `text-sm text-slate-600`
- `TABLE_CELL_MONO_CLASS`: `text-[13px] font-mono font-medium text-slate-500`
- `FORM_LABEL_CLASS`: `text-sm font-semibold text-slate-700`
- `FORM_INPUT_CLASS`: `h-11 border-slate-200 focus:ring-slate-100 focus:border-slate-900`

## Consequences
- Pros: Visual consistency, easier maintenance (change once, update everywhere).
- Cons: One-time refactor cost of multiple files.
- Requirement: All NEW tables and forms MUST use these constants.
