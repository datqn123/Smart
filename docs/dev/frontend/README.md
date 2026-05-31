# docs/ — Tài liệu sản phẩm & dự án

Thư mục này gom **tài liệu phục vụ phát triển phần mềm** (domain, hợp đồng API, SRS, ADR, database mô tả, báo cáo).

**Tài liệu dành cho Agent** (template, context index, planner brief): nằm trong **[`AGENTS/docs/`](../AGENTS/docs/README.md)**. Stub chuyển hướng (nếu còn link cũ): [`CONTEXT_INDEX.md`](CONTEXT_INDEX.md), [`templates/README.md`](templates/README.md).

## Cấu trúc chính (rút gọn)

| Thư mục | Nội dung |
| :------- | :-------- |
| `api/` | Thiết kế API REST (`API_PROJECT_DESIGN.md`, `API_Task*.md`) — dùng chung FE + **Spring Boot** |
| `UC/` | Use case, schema SQL, đặc tả DB |
| `database/` | Mô tả bảng / quan hệ (tham chiếu triển khai) |
| `ba/` | Output BA (elicitation, PRD, USS, …) |
| `srs/` | SRS theo task |
| `adr/` | Architecture Decision Records |
| `analysis/`, `sync_reports/`, `reports/`, `tech_lead/` | Báo cáo & alignment theo task |
| `rules/` | Quy tắc UI/doc bổ sung (khác `RULES.md` ở root) |

**Quy tắc coding FE**: [`RULES.md`](../RULES.md) (root repo).

**Điều phối Agent**: [`AGENTS/AGENT_REGISTRY.md`](../AGENTS/AGENT_REGISTRY.md).
