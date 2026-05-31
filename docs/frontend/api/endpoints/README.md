# Index endpoint theo Task (phục vụ API_BRIDGE / Doc Sync)

Mỗi task có **một** file `TaskXXX.md` trong thư mục này: bảng **Path | Method | Spec | Mẫu request/response JSON | Postman (Tester)**.

**Mẫu JSON thuần** (body request hoặc envelope response) nằm tại [`../samples/TaskXXX/`](../samples/) — `API_BRIDGE` đọc nhanh shape mà không cần parse toàn bộ spec Markdown.

**Postman** (wrapper `_description` + `request` + `headers` + `body`): [`backend/smart-erp/docs/postman/`](../../../../backend/smart-erp/docs/postman/) — chuẩn **3 file** theo `TESTER_AGENT_INSTRUCTIONS.md`; Doc Sync giữ **cùng field** với `samples/*/.*.request.json` khi đổi contract.
