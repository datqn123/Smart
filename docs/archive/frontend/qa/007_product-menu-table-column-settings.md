# QA Spec - Product Menu Table Column Settings

> Agent: QA_SPEC_WRITER  
> Ngay cap nhat: 01/06/2026  
> Trang thai: QA_READY_FOR_CODING

## 1. Test Matrix

- GET `table-columns?scope=all` tra ve du 7 table.
- PUT settings voi 4 key San pham:
  - Admin/Owner pass.
  - Staff fail 403.
- Validate payload:
  - tableKey khong hop le -> 400
  - column key khong hop le -> 400
  - required column trong hidden -> 400
  - duplicate columnOrder -> 400
- UI settings page:
  - dropdown hien du 7 bang.
  - save xong toast thanh cong.
- Product pages:
  - `/products/categories`, `/products/list`, `/products/suppliers`, `/products/customers`
  - table nhan dung hidden/order theo setting moi.
  - select/action columns van hien.
- Regression:
  - 3 page inventory cu van nhan setting dung.

## 2. Smoke Commands

- Backend: `mvnw -q -DskipTests compile`
- Frontend: `npm run build`

## 3. Manual Scenarios

- Scenario A: an cot `Gia ban` tren `San pham`, reload `/products/list`.
- Scenario B: doi thu tu cot tren `Khach hang`, reload voi account khac.
- Scenario C: backend settings API loi, 4 page san pham fallback default va khong crash.
