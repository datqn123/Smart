# Skill: CodeGraph Context

Use this shared skill whenever an agent needs to discover relevant code, estimate blast radius, identify callers/callees, or choose tests before changing or reviewing Smart ERP code.

CodeGraph is a context and impact layer. It helps agents find the right files and symbols faster, but it does not replace reading source files, `rg`, tests, or project docs.

## Availability

This repo has CodeGraph configured through `.mcp.json`:

```json
{
  "mcpServers": {
    "codegraph": {
      "type": "stdio",
      "command": "codegraph",
      "args": ["serve", "--mcp"]
    }
  }
}
```

The local index lives under `.codegraph/`. Treat `.codegraph/codegraph.db` as local machine state, not a project artifact to edit or commit.

## Preferred Tool Order

1. Prefer CodeGraph MCP tools when they are available in the session:
   - `mcp__codegraph__codegraph_status`
   - `mcp__codegraph__codegraph_search`
   - `mcp__codegraph__codegraph_context`
   - `mcp__codegraph__codegraph_callers`
   - `mcp__codegraph__codegraph_callees`
   - `mcp__codegraph__codegraph_impact`
   - `mcp__codegraph__codegraph_node`

2. If MCP tools are unavailable, use CLI fallback:

```powershell
codegraph status --json
codegraph query "<symbol-or-feature>" --json
codegraph context "<task description>" --format json
codegraph callers "<symbol>" --json
codegraph callees "<symbol>" --json
codegraph impact "<symbol>" --json
codegraph affected <changed-files> --json
```

3. After CodeGraph identifies files or symbols, read the relevant source files directly before making decisions.

## Required Freshness Check

Before relying on CodeGraph for scope, impact, or tests:

1. Run `codegraph status --json` or the MCP status tool.
2. If `initialized` is not `true`, fall back to `rg` and file reads.
3. If `pendingChanges.added`, `pendingChanges.modified`, or `pendingChanges.removed` is non-zero, run:

```powershell
codegraph sync
```

4. Re-run status after sync before using CodeGraph results for decisions.

## Visible Preflight Requirement

Agents must make CodeGraph usage visible in the transcript for every code-affecting task.

Required behavior:

- First progress update: mention `CodeGraph preflight`.
- First tool batch: run MCP status/context/search/impact/affected or CLI fallback before broad manual scanning.
- If CodeGraph cannot run: say `CodeGraph unavailable` and explain fallback before using `rg` or file reads.
- Final response: include `CodeGraph: <operations used>` or `CodeGraph: unavailable, used <fallback>`.
- If the agent already started with `rg`, `Get-Content`, or direct file reads without CodeGraph, stop broad scanning and restart discovery with CodeGraph.

## Usage By Workflow Stage

### SRS Writer

Use CodeGraph to discover candidate evidence:

```powershell
codegraph context "<feature or bug request>" --format json
codegraph query "<domain symbol, route, page, service, table>" --json
```

Record relevant `relatedFiles`, routes, services, components, graph nodes, and tests as SRS traceability evidence.

### Tech Spec Writer

Use CodeGraph to define blast radius and handoff files:

```powershell
codegraph impact "<symbol>" --json
codegraph callers "<symbol>" --json
codegraph callees "<symbol>" --json
```

Use results to list files to read/edit, dependency risks, and cross-layer contracts. Verify by reading the source.

### QA Spec Writer

Use CodeGraph to identify regression and affected tests:

```powershell
codegraph affected <changed-or-expected-source-files> --json
codegraph context "<feature test scope>" --format json
```

Use results to seed the test matrix; add missing tests when CodeGraph cannot find coverage.

### Coding Agent

Use CodeGraph before editing:

```powershell
codegraph context "<implementation task>" --format json
codegraph query "<symbol>" --json
codegraph impact "<symbol>" --json
```

Before running tests, use:

```powershell
codegraph affected <changed-files> --json
```

Run focused tests from CodeGraph plus any tests required by the handoff.

### Code Review Agent

Use CodeGraph to review cross-scope impact:

```powershell
codegraph impact "<changed symbol>" --json
codegraph callers "<changed symbol>" --json
codegraph callees "<changed symbol>" --json
codegraph affected <changed-files> --json
```

Findings must still be grounded in exact file and line references from the source or diff.

## Guardrails

- Do not treat CodeGraph output as authoritative when source files disagree.
- Do not skip horizontal analysis just because CodeGraph returns few files.
- Do not commit `.codegraph/codegraph.db`, WAL/SHM files, cache, or logs.
- If CodeGraph is unavailable, continue with `rg`, direct file reads, and existing project docs.
- For AI agentic work, CodeGraph helps discover code but does not change the architecture rule: LangGraph orchestrates, Harness executes/validates, tools stay scoped.
