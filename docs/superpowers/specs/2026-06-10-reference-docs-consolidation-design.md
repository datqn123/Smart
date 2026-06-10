# Reference Docs Consolidation — Design Spec

## Problem

- `docs/reference/` (agent's single source of truth) is incomplete: `tables/` empty, `api-contracts/` missing, `use-cases/` missing
- `docs/dev/frontend/api/` contains 100+ outdated `API_Task*.md` and 90+ `BRIDGE` files that mislead agents
- `.opencode/instructions.md` tells agents to read `docs/dev/`, causing confusion
- No structured API contracts exist for agents to reference

## Scope

1. Generate `docs/reference/tables/` from live DB schema
2. Create `docs/reference/api-contracts/` with per-module endpoint docs
3. Delete outdated API docs from `docs/dev/frontend/api/`
4. Update `.opencode/instructions.md` to point agents to `reference/` only
5. Update `docs/README.md`

**Out of scope:** use-cases/, sql/, archive cleanup.

## Design

### 1. Tables — auto-generated

Run `python scripts/db-docs.py` to produce:

```
docs/reference/tables/
├── README.md
├── core_tables.md
├── indexes.md
└── foreign_keys.md
```

Always reflects actual DB via Flyway migrations.

### 2. API Contracts — per module

```
docs/reference/api-contracts/
├── auth.md
├── users.md
├── catalog.md
├── inventory.md
├── sales.md
├── finance.md
├── ai.md
├── dashboard.md
├── notifications.md
├── settings.md
└── custom-interface.md
```

Each file documents every endpoint in that module.

Format per endpoint:

```
### METHOD /api/v1/<path>
- **Mô tả:** <Vietnamese description>
- **Auth:** Public | JWT [required permission]
- **Request body:**
  ```json
  { "<field>": "<type>"  /* mandatory/optional, description */ }
  ```
- **Response 200:**
  ```json
  { "<field>": "<type>"  /* description */ }
  ```
- **Errors:** <HTTP status codes>
```

### 3. Cleanup

Delete entire `docs/dev/frontend/api/` directory (Task*.md, BRIDGE*.md, samples/).

Keep other `docs/dev/` content (ADR, database schema docs, project overview).

### 4. Instructions update

`.opencode/instructions.md` changes:

- **reference/** → agent MUST read
- **dev/** → agent DO NOT read (architecture reference only)
- **archive/** → DO NOT read
- **tests/** → DO NOT read

## Implementation order

1. Delete outdated API docs in `docs/dev/frontend/api/`
2. Run `scripts/db-docs.py` → generate `docs/reference/tables/`
3. Write API contract files by reading each controller + DTO from backend code
4. Update `.opencode/instructions.md`
5. Update `docs/README.md`
