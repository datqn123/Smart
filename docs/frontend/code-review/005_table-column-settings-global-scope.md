# Code Review - Table Column Settings Global Scope

> Agent: CODE_REVIEW_AGENT  
> Ngay cap nhat: 01/06/2026  
> Trang thai: REVIEW_PASS_WITH_NOTES

## 1. Findings

- Khong phat hien regression blocking trong diff hien tai.
- Gate save global da co 2 lop:
  - `@PreAuthorize("can_manage_inventory && can_manage_staff")`
  - role claim `Owner|Admin` trong service.
- Frontend da bo localStorage-only source-of-truth, chuyen qua backend GET/PUT va van co fallback default.

## 2. Residual Risks

- Du lieu cu trong `user_table_column_settings` khong duoc migrate sang global table trong dot nay.
- `GET` settings van mo cho `can_manage_inventory`; neu can mo rong nguoi xem kho khac role thi can bo sung authority map sau.

## 3. Verification

- Frontend:
  - `npm run build` pass.
  - `npm run test -- mockCatalog` pass.
- Backend:
  - `mvnw -q -DskipTests compile` pass.
