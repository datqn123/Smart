-- Task103 — SRS_Task103_ai-table-description-registry + docs/plans/existing/feature/spring_ai_table_description_registry.plan.md
-- Bảng registry mô tả nghiệp vụ theo bảng PostgreSQL cho downstream AI (ai_python merge SchemaArtifact.tables[].name).
-- Không tạo schema riêng: giữ public như các bảng nghiệp vụ snake_case gần đây (vd. cash_funds).

CREATE TABLE IF NOT EXISTS ai_table_description (
    id           BIGSERIAL PRIMARY KEY,
    table_name   VARCHAR(128) NOT NULL,
    description  TEXT           NOT NULL DEFAULT '',
    created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_ai_table_description_name_lower
        CHECK (table_name = lower(table_name)),
    CONSTRAINT ck_ai_table_description_name_nonempty
        CHECK (length(trim(table_name)) > 0),
    CONSTRAINT uq_ai_table_description_table_name UNIQUE (table_name)
);

COMMENT ON TABLE ai_table_description IS
    'Registry mô tả bảng cho AI: một dòng / tên bảng vật lý (chữ thường). Join với SchemaArtifact.tables[].name khi YAML dùng tên đã chuẩn hóa lowercase.';

COMMENT ON COLUMN ai_table_description.table_name IS
    'Tên bảng PostgreSQL (unquoted → lowercase), duy nhất.';

COMMENT ON COLUMN ai_table_description.description IS
    'Mô tả nghiệp vụ tiếng Việt hoặc đa ngôn ngữ theo quy ước vận hành.';

-- Seed mô tả nghiệp vụ (idempotent) — tên bảng = tên vật lý PostgreSQL (identifier không ngoặc → lowercase).
-- Nguồn bảng: V1 baseline + V3 refresh_tokens + V12/V19/V24/V35/V41; SRS Task103.
INSERT INTO ai_table_description (table_name, description)
SELECT v.table_name, v.description
FROM (
    VALUES
        ('roles', 'Vai trò người dùng (Owner, Staff, Admin) và tập quyền JSON trên menu/thao tác.'),
        ('categories', 'Cây danh mục sản phẩm: mã, tên, phân cấp cha-con, thứ tự hiển thị, trạng thái.'),
        ('suppliers', 'Nhà cung cấp: mã, liên hệ, trạng thái; liên kết phiếu nhập.'),
        ('customers', 'Khách hàng: thông tin mua hàng, mã, trạng thái; liên kết đơn bán.'),
        ('warehouselocations', 'Vị trí / khu vực lưu kho trong kho hàng (kệ, khu, mã vị trí).'),
        ('users', 'Tài khoản đăng nhập: email, vai trò, trạng thái Active/Locked, mã nhân viên.'),
        ('products', 'Sản phẩm master: SKU, tên, đơn vị cơ sở, giá, danh mục, trạng thái kinh doanh.'),
        ('productimages', 'Ảnh sản phẩm: URL Cloudinary (hoặc nguồn khác), cờ ảnh chính, thứ tự.'),
        ('alertsettings', 'Ngưỡng cảnh báo tồn kho / hết hạn theo cấu hình người dùng hoặc hệ thống.'),
        ('systemlogs', 'Nhật ký hệ thống: thao tác quan trọng, entity, payload tóm tắt (audit).'),
        ('financeledger', 'Sổ cái kế toán: bút toán nợ/có, số dư lũy kế, liên kết chứng từ nguồn và quỹ.'),
        ('aiinsights', 'Bản ghi insight/gợi ý AI (legacy hoặc báo cáo tự động theo module AI).'),
        ('aichathistory', 'Lịch sử hội thoại chat AI (prompt/response tóm tắt theo thiết kế bảo mật).'),
        ('mediaaudits', 'Theo dõi thay đổi tệp media (upload/xóa) phục vụ truy vết.'),
        ('productunits', 'Đơn vị quy đổi của sản phẩm: hệ số so với đơn vị cơ sở, quy tắc làm tròn.'),
        ('productpricehistory', 'Lịch sử thay đổi giá niêm yết / giá bán theo thời gian.'),
        ('inventory', 'Tồn kho theo sản phẩm, lô, vị trí kho: số lượng, hạn dùng, trạng thái lô.'),
        ('stockreceipts', 'Phiếu nhập kho: nhà cung cấp, trạng thái duyệt, người tạo, ngày nhập.'),
        ('salesorders', 'Đơn hàng bán (bán buôn/bán lẻ): khách, kênh, thanh toán, trạng thái giao hàng.'),
        ('stockreceiptdetails', 'Dòng chi tiết phiếu nhập: sản phẩm, số lượng, đơn giá, lô.'),
        ('orderdetails', 'Dòng chi tiết đơn hàng: SKU, số lượng đặt, đơn giá, chiết khấu, đã giao.'),
        ('stockdispatches', 'Phiếu xuất kho / giao hàng: loại xuất, trạng thái, liên kết đơn bán hoặc điều chuyển.'),
        ('inventorylogs', 'Nhật ký biến động từng lô tồn (nhập, xuất, điều chỉnh, kiểm kê).'),
        ('notifications', 'Thông báo in-app: loại, đã đọc, liên kết thực thể nghiệp vụ (phiếu, yêu cầu…).'),
        ('storeprofiles', 'Hồ sơ cửa hàng / POS: tên hiển thị, logo, kho mặc định bán lẻ.'),
        ('cashtransactions', 'Phiếu thu chi: loại, số tiền, danh mục, quỹ, người thực hiện, liên kết sổ cái.'),
        ('partnerdebts', 'Công nợ đối tác: phát sinh, thanh toán, trạng thái, người tạo.'),
        ('staffpasswordresetrequests', 'Yêu cầu đặt lại mật khẩu nhân viên (Owner duyệt / quy trình email).'),
        ('inventoryauditsessions', 'Đợt kiểm kê kho: phạm vi, trạng thái, ngày hoàn thành, lý do hủy.'),
        ('inventoryauditlines', 'Dòng kiểm kê theo lô: số lệch, ghi chú, áp dụng điều chỉnh tồn.'),
        ('refresh_tokens', 'Refresh token OAuth: họ JWT, thiết bị, hết hạn, thu hồi đăng xuất.'),
        ('vouchers', 'Mã khuyến mãi / voucher: giá trị, điều kiện, thời hạn, kênh áp dụng (POS/bán buôn).'),
        ('voucher_redemptions', 'Lượt quét/sử dụng voucher gắn đơn hàng hoặc giao dịch bán lẻ.'),
        ('inventory_audit_session_events', 'Sự kiện timeline phiên kiểm kê (tạo, cập nhật, hủy, hoàn tất).'),
        ('stockdispatch_lines', 'Chi tiết dòng phiếu xuất: sản phẩm, số lượng, đơn giá; hỗ trợ xóa mềm dòng.'),
        ('cash_funds', 'Danh mục quỹ tiền (tiền mặt, tài khoản ngân hàng); mặc định cho thu chi và sổ cái.'),
        ('ai_table_description', 'Registry mô tả nghiệp vụ theo tên bảng cho prompt AI; join với schema YAML.')
) AS v(table_name, description)
WHERE NOT EXISTS (
    SELECT 1 FROM ai_table_description t WHERE t.table_name = v.table_name
);
