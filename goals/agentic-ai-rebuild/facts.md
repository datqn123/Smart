# Facts — Agentic AI Rebuild (ai_python)

## Harness & Auth
- Harness xác thực mỗi request (JWT/Cookie) trước khi xử lý; request không hợp lệ bị từ chối, không vào pipeline.
- Harness map User_ID ra Thread_ID tương ứng; pipeline nhận thread_id đã resolve, không tự xử lý auth.

## Session Manager (planner / evaluator)
- Session Manager đọc skill .md của chính nó khi phiên làm việc lớn bắt đầu.
- Session Manager xuất structured JSON decision với action thuộc {call_tool, retry_tool, replan, request_clarification, finish}; LLM chỉ quyết action + tool_name + data cần forward, KHÔNG tự dựng payload.
- Dispatcher map tool_name ra đúng subgraph và gọi nó; payload luôn gồm raw_require của user + upstream_data mà SM chỉ định lấy từ tool trước.
- Khi data trả về không ổn, Session Manager đọc LẠI skill .md của mình trước khi phân tích lại require.
- Session Manager phân biệt lỗi do tool vs lỗi do plan sai, từ đó chọn retry_tool (lỗi tool) hoặc replan (lỗi plan).

## Tools & Skill loader
- Mỗi tool là một LangGraph subgraph có node load_skill chạy ĐẦU TIÊN, đọc file .md của tool đó.
  - **Bổ sung:** mỗi tool phải có cơ chế tự validate data output của chính mình trước khi trả về, để hạn chế data sai làm ảnh hưởng các step sau.
- Khi một tool bị retry, subgraph chạy lại từ đầu nên node load_skill đọc lại .md mỗi lần retry.
- Mỗi skill .md gồm 6 phần: Role, Nhiệm vụ, Input contract, Constraints/Rules, Output schema, Few-shot examples.
- Registry là static — danh sách tool + mô tả được nhét vào context của Session Manager; SM chỉ gọi được tool có đăng ký trong registry.

## sql_execute
- Tool sql_execute kết nối database read-only, sinh SQL từ require và chạy để lấy data.
- SQL guard chặn mọi câu không phải truy vấn đọc (INSERT/UPDATE/DELETE/DROP/ALTER...): không thực thi và trả lỗi an toàn; read-only được enforce ở tầng kết nối DB chứ không chỉ dựa vào LLM.

## data_validator (bắt buộc trước composer)
- Tool data_validator chạy BẮT BUỘC trước answer_composer; answer_composer không bao giờ chạy trước validator.
- data_validator đọc raw require của user + data cuối cùng và phán quyết data có phù hợp require hay không.
- Khi data_validator phán data KHÔNG phù hợp require, hệ thống trigger HITL: phiên lớn tạm dừng, hỏi lại user, chờ clarification_response rồi resume.
  - **Lưu ý:** hiện CHƯA có cơ chế pause để hỏi user — build này phải tạo mới hạ tầng pause/resume cho HITL.

## answer_composer
- Tool answer_composer soạn câu trả lời cho user từ data các step trước + raw require, chỉ chạy sau khi validator pass.
  - **Bổ sung:** câu trả lời phải lịch sự, cung cấp đủ thông tin cho user, và gợi ý bước tiếp theo cho user.

## Output
- Kết quả trả về user qua SSE streaming; SSE contract được dựng lại trong build này.

## Config
- Module config kết nối LLM Qwen3.6 27B qua API; mọi tool dùng chung LLM client này.
- Module config kết nối backend API — endpoint nhận require user mà Spring gửi sang ai_python.

## Budget & Safety
- Phiên lớn có giới hạn max_steps và giới hạn retry mỗi tool; chạm giới hạn thì dừng an toàn và báo, không lặp vô hạn.

## Out of scope (vòng sau)
- Build này chạy stateless — mỗi require xử lý độc lập, CHƯA tích hợp conversation memory (memory để vòng sau).
