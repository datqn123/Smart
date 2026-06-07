"""Small ERP guide harness tool."""

from __future__ import annotations

from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


class ErpGuideTool:
    manifest = ToolManifest(
        name="erp_guide",
        description="Return concise ERP domain guidance for intent/planner context.",
        args_schema='{"topic":"string"}',
        capability="erp_guide",
        output_schema='{"guidance": "string"}',
        when_to_use="Planner needs ERP domain terminology or guidance to interpret the goal.",
        when_not_to_use="The goal needs actual data (use sql_query) or a record (use a draft tool).",
        risk_level="low",
        side_effect_class="read_only",
        produces=("guidance",),
        examples=("phiếu nhập là gì", "quy trình bán hàng"),
    )

    async def invoke(self, args: dict, ctx: TurnContext) -> ToolResult:
        _ = ctx
        topic = str(args.get("topic") or "erp").lower()
        if "inventory" in topic or "kho" in topic:
            text = "Kho hàng gồm tồn kho hiện tại, nhập kho, xuất kho và cảnh báo sắp hết hàng."
        elif "finance" in topic or "doanh thu" in topic:
            text = "Tài chính gồm doanh thu, chi phí, công nợ và dòng tiền; dữ liệu nhạy cảm cần kiểm tra quyền."
        else:
            text = "Smart ERP quản lý sản phẩm, kho, đơn hàng, khách hàng, nhà cung cấp và tài chính."
        return ToolResult(ok=True, output={"topic": topic, "guide": text}, observation_text=text)
