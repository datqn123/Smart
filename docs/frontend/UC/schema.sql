-- ============================================================
-- SMART INVENTORY MANAGEMENT - PostgreSQL Schema
-- Version: 5.2 — bổ sung theo API spec / Database_Specification: SalesOrders (kênh/thanh toán), StoreProfiles,
--           CashTransactions, PartnerDebts, StaffPasswordResetRequests, InventoryAuditSessions/Lines (+ variance_applied_at)
-- Database: PostgreSQL 15+
-- Ngày tạo: 11/04/2026
-- Dự án: Đồ án Tốt nghiệp - Quản lý Kho thông minh
-- Tham chiếu: Database_Schema_Detail.md v4.0
--             UseCase_Database_Coverage.md (UC1-UC13)
--             Schema_Simplified.md
--             Add_ProductImages_Table.md
-- ============================================================

-- Xóa database cũ nếu cần (uncomment khi development)
-- DROP DATABASE IF EXISTS smart_inventory;
-- CREATE DATABASE smart_inventory WITH ENCODING 'UTF8';

-- ============================================================
-- BƯỚC 1: NHÓM BẢNG CỐT LÕI (Không chứa Khóa Ngoại)
-- ============================================================

-- 1. Roles (Vai trò)
-- UC3: Manage Staff Accounts
CREATE TABLE Roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,
    permissions JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  Roles IS 'Vai trò người dùng: Owner, Staff, Admin';
COMMENT ON COLUMN Roles.permissions IS 'JSON quyền hạn. VD: {"can_approve": true, "can_delete": false}';

-- 2. Categories (Danh mục sản phẩm)
-- UC6, UC8: Manage inventory list, Manage Products
CREATE TABLE Categories (
    id            SERIAL       PRIMARY KEY,
    category_code VARCHAR(50)  NOT NULL UNIQUE,
    name          VARCHAR(255) NOT NULL,
    description   TEXT,
    parent_id     INT,
    sort_order    INT          NOT NULL DEFAULT 0,
    status        VARCHAR(20)  NOT NULL DEFAULT 'Active'
                               CHECK (status IN ('Active', 'Inactive')),
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_categories_parent
        FOREIGN KEY (parent_id) REFERENCES Categories(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE Categories IS 'Danh mục sản phẩm phân cấp (hierarchical tree)';

-- 3. Suppliers (Nhà cung cấp)
-- UC7, UC8, UC12: Manage stock receipts, Manage Products, Update via Image
CREATE TABLE Suppliers (
    id             SERIAL       PRIMARY KEY,
    supplier_code  VARCHAR(50)  NOT NULL UNIQUE,
    name           VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone          VARCHAR(20),
    email          VARCHAR(255),
    address        TEXT,
    tax_code       VARCHAR(50),
    status         VARCHAR(20)  NOT NULL DEFAULT 'Active'
                                CHECK (status IN ('Active', 'Inactive')),
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE Suppliers IS 'Nhà cung cấp hàng hóa. Mã tự sinh: NCC0001';

CREATE INDEX idx_suppliers_name  ON Suppliers(name);
CREATE INDEX idx_suppliers_phone ON Suppliers(phone);

-- 4. Customers (Khách hàng)
-- UC9: Manage Sales Orders
CREATE TABLE Customers (
    id             SERIAL       PRIMARY KEY,
    customer_code  VARCHAR(50)  NOT NULL UNIQUE,
    name           VARCHAR(255) NOT NULL,
    phone          VARCHAR(20)  NOT NULL,
    email          VARCHAR(255),
    address        TEXT,
    loyalty_points INT          NOT NULL DEFAULT 0,
    status         VARCHAR(20)  NOT NULL DEFAULT 'Active'
                                CHECK (status IN ('Active', 'Inactive')),
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  Customers IS 'Khách hàng. Mã tự sinh: KH00001. total_spent tính qua SUM(SalesOrders.total_amount)';
COMMENT ON COLUMN Customers.loyalty_points IS 'Điểm tích lũy, tính tự động từ đơn hàng';

CREATE INDEX idx_customers_phone ON Customers(phone);

-- 5. WarehouseLocations (Vị trí kho / Kệ)
-- UC6, UC10, UC13: Manage inventory, Dispatch, Voice update
CREATE TABLE WarehouseLocations (
    id             SERIAL       PRIMARY KEY,
    warehouse_code VARCHAR(20)  NOT NULL,
    shelf_code     VARCHAR(20)  NOT NULL,
    description    VARCHAR(255),
    capacity       DECIMAL(8,2),
    status         VARCHAR(20)  NOT NULL DEFAULT 'Active'
                                CHECK (status IN ('Active', 'Maintenance', 'Inactive')),
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_warehouse_shelf UNIQUE (warehouse_code, shelf_code)
);

COMMENT ON TABLE WarehouseLocations IS 'Vị trí lưu trữ trong kho. VD: WH01-A1, WH01-B2';

-- ============================================================
-- BƯỚC 2: NHÓM BẢNG ĐỊNH TUYẾN (Phụ thuộc Bước 1)
-- ============================================================

-- 6. Users (Người dùng)
-- Dùng trong hầu hết UC (UC1-UC13): Auth, Audit Trail
CREATE TABLE Users (
    id            SERIAL       PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    phone         VARCHAR(20),
    role_id       INT          NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'Active'
                               CHECK (status IN ('Active', 'Locked')),
    last_login    TIMESTAMP,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id) REFERENCES Roles(id)
        ON DELETE RESTRICT
);

COMMENT ON TABLE  Users IS 'Người dùng hệ thống. Password dùng bcrypt/argon2';
COMMENT ON COLUMN Users.password_hash IS 'Mật khẩu mã hóa bằng bcrypt hoặc argon2';

CREATE INDEX idx_users_phone ON Users(phone);

-- 6b. RefreshTokens (Task001 / Task003 — JWT refresh, revoke mở rộng sau)
CREATE TABLE RefreshTokens (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_refresh_tokens_user
        FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_user_id ON RefreshTokens(user_id);

COMMENT ON TABLE RefreshTokens IS 'Refresh token đăng nhập (opaque). Flyway backend: V3__task001_refresh_tokens.sql (bảng refresh_tokens snake_case PostgreSQL).';

-- 7. Products (Sản phẩm)
-- UC1, UC6, UC7, UC8, UC9, UC10, UC11, UC12, UC13
CREATE TABLE Products (
    id          SERIAL       PRIMARY KEY,
    category_id INT,
    sku_code    VARCHAR(50)  NOT NULL UNIQUE,
    barcode     VARCHAR(100),
    name        VARCHAR(255) NOT NULL,
    image_url   VARCHAR(500),
    description TEXT,
    weight      DECIMAL(8,2),
    status      VARCHAR(20)  NOT NULL DEFAULT 'Active'
                             CHECK (status IN ('Active', 'Inactive')),
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES Categories(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE  Products IS 'Sản phẩm hàng hóa. SKU và Barcode duy nhất';
COMMENT ON COLUMN Products.weight IS 'Trọng lượng đơn vị (gram)';

CREATE INDEX idx_products_sku     ON Products(sku_code);
CREATE INDEX idx_products_barcode ON Products(barcode);
CREATE INDEX idx_products_name    ON Products(name);
CREATE INDEX idx_products_status  ON Products(status);

-- 7.1 ProductImages (Hình ảnh sản phẩm)
-- UC8, UC12: Manage Products, Update via Image
CREATE TABLE ProductImages (
    id              SERIAL       PRIMARY KEY,
    product_id      INT          NOT NULL,
    image_url       VARCHAR(500) NOT NULL,
    alt_text        VARCHAR(255),
    is_primary      BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order      INT          NOT NULL DEFAULT 0,
    file_size_bytes INT,
    mime_type       VARCHAR(100),
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pi_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE  ProductImages IS 'Quản lý nhiều hình ảnh cho mỗi sản phẩm. 1 sản phẩm có thể có nhiều ảnh';
COMMENT ON COLUMN ProductImages.is_primary IS 'Ảnh đại diện. Mỗi sản phẩm chỉ có 1 ảnh chính';
COMMENT ON COLUMN ProductImages.sort_order IS 'Thứ tự hiển thị. Số nhỏ hiển thị trước';

CREATE INDEX idx_pi_product  ON ProductImages(product_id);
CREATE INDEX idx_pi_primary  ON ProductImages(product_id, is_primary);

-- ============================================================
-- BƯỚC 3: NHÓM BẢNG VỆ TINH & HỆ THỐNG
-- (Phụ thuộc Users & Products)
-- ============================================================

-- 8. AlertSettings (Cấu hình cảnh báo)
-- UC5: Configure Alert Settings
CREATE TABLE AlertSettings (
    id              SERIAL       PRIMARY KEY,
    owner_id        INT          NOT NULL,
    alert_type      VARCHAR(30)  NOT NULL
                                 CHECK (alert_type IN ('LowStock', 'ExpiryDate', 'HighValueTransaction', 'PendingApproval', 'PartnerDebtDueSoon')),
    threshold_value DECIMAL(10,2),
    channel         VARCHAR(20)  NOT NULL
                                 CHECK (channel IN ('App', 'Email', 'SMS', 'Zalo')),
    frequency       VARCHAR(20)  NOT NULL DEFAULT 'Realtime'
                                 CHECK (frequency IN ('Realtime', 'Daily', 'Weekly')),
    is_enabled      BOOLEAN      NOT NULL DEFAULT TRUE,
    recipients      JSONB,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_alert_owner
        FOREIGN KEY (owner_id) REFERENCES Users(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE  AlertSettings IS 'Cấu hình cảnh báo theo từng Owner';
COMMENT ON COLUMN AlertSettings.recipients IS 'JSON danh sách người nhận bổ sung. VD: ["user_2","user_5"]';

CREATE INDEX idx_alert_owner ON AlertSettings(owner_id);

-- 9. SystemLogs (Nhật ký Hệ thống)
-- UC4, UC6: Approve Transactions, Manage inventory
CREATE TABLE SystemLogs (
    id           SERIAL       PRIMARY KEY,
    log_level    VARCHAR(20)  NOT NULL
                              CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module       VARCHAR(100) NOT NULL,
    action       VARCHAR(255) NOT NULL,
    user_id      INT,
    message      TEXT         NOT NULL,
    stack_trace  TEXT,
    context_data JSONB,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_syslog_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE SystemLogs IS 'Nhật ký hệ thống. Cân nhắc partitioning theo tháng hoặc archiving sau 90 ngày';

CREATE INDEX idx_syslog_level      ON SystemLogs(log_level);
CREATE INDEX idx_syslog_created_at ON SystemLogs(created_at);

-- 10. FinanceLedger (Sổ cái tài chính)
-- UC1, UC4: Dashboard, Approve Transactions
CREATE TABLE FinanceLedger (
    id               SERIAL       PRIMARY KEY,
    transaction_date DATE         NOT NULL,
    transaction_type VARCHAR(30)  NOT NULL
                                  CHECK (transaction_type IN ('SalesRevenue', 'PurchaseCost', 'OperatingExpense', 'Refund')),
    reference_type   VARCHAR(50),
    reference_id     INT          NOT NULL,
    amount           DECIMAL(10,2) NOT NULL,
    description      TEXT,
    created_by       INT          NOT NULL,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_finance_created_by
        FOREIGN KEY (created_by) REFERENCES Users(id)
        ON DELETE RESTRICT
);

COMMENT ON TABLE  FinanceLedger IS 'Sổ cái tài chính. reference_type+reference_id là Polymorphic FK (validate ở application layer)';
COMMENT ON COLUMN FinanceLedger.amount IS 'Dương = thu, Âm = chi';
COMMENT ON COLUMN FinanceLedger.reference_type IS 'Loại chứng từ: SalesOrder, StockReceipt, etc.';

CREATE INDEX idx_finance_date ON FinanceLedger(transaction_date);
CREATE INDEX idx_finance_type ON FinanceLedger(transaction_type);

-- 11. AIInsights (Phân tích kinh doanh AI)
-- UC1, UC2: Dashboard, AI Business Insight
CREATE TABLE AIInsights (
    id                 SERIAL       PRIMARY KEY,
    owner_id           INT          NOT NULL,
    dashboard_snapshot JSONB        NOT NULL,
    prompt             TEXT         NOT NULL,
    ai_advice          TEXT         NOT NULL,
    model_used         VARCHAR(100),
    tokens_used        INT,
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ai_insight_owner
        FOREIGN KEY (owner_id) REFERENCES Users(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE  AIInsights IS 'Lịch sử phân tích kinh doanh bằng AI (Deepseek)';
COMMENT ON COLUMN AIInsights.dashboard_snapshot IS 'JSON snapshot dashboard tại thời điểm phân tích';
COMMENT ON COLUMN AIInsights.ai_advice IS 'Kết quả trả về từ LLM, format Markdown';

CREATE INDEX idx_ai_insight_owner ON AIInsights(owner_id);

-- 12. AIChatHistory (Lịch sử Chat Bot)
-- UC2, UC11: AI Insight, Interact with ChatBot
CREATE TABLE AIChatHistory (
    id               SERIAL       PRIMARY KEY,
    user_id          INT          NOT NULL,
    session_id       VARCHAR(100),
    message          TEXT         NOT NULL,
    sender           VARCHAR(10)  NOT NULL
                                  CHECK (sender IN ('User', 'Bot')),
    intent           JSONB,
    response_time_ms INT,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chat_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE  AIChatHistory IS 'Lịch sử tương tác ChatBot. Cân nhắc partition theo tháng do dữ liệu tăng nhanh';
COMMENT ON COLUMN AIChatHistory.intent IS 'JSON ý định nhận dạng. VD: {"action":"check_stock","product":"Sữa ông Thọ","location":"A1"}';

CREATE INDEX idx_chat_user       ON AIChatHistory(user_id);
CREATE INDEX idx_chat_session    ON AIChatHistory(session_id);
CREATE INDEX idx_chat_created_at ON AIChatHistory(created_at);

-- 13. MediaAudits (Lưu vết Media Cloud)
-- UC12, UC13: Update via Image, Update via Voice
CREATE TABLE MediaAudits (
    id              SERIAL        PRIMARY KEY,
    file_type       VARCHAR(20)   NOT NULL
                                  CHECK (file_type IN ('OCR_Image', 'Voice_Audio')),
    cloud_url       VARCHAR(1000) NOT NULL,
    entity_type     VARCHAR(50)   NOT NULL,
    entity_id       INT           NOT NULL,
    file_size_bytes INT,
    mime_type       VARCHAR(100),
    uploaded_by     INT,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_media_uploader
        FOREIGN KEY (uploaded_by) REFERENCES Users(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE  MediaAudits IS 'Lưu vết file media trên Cloud. entity_type+entity_id là Polymorphic FK (validate ở application layer)';
COMMENT ON COLUMN MediaAudits.cloud_url IS 'URL S3/Firebase endpoint';
COMMENT ON COLUMN MediaAudits.entity_type IS 'Loại đối tượng: StockReceipt, SalesOrder, Inventory';

-- 14. ProductUnits (Đơn vị tính quy đổi)
-- UC6, UC7, UC8, UC9, UC10, UC13
CREATE TABLE ProductUnits (
    id              SERIAL       PRIMARY KEY,
    product_id      INT          NOT NULL,
    unit_name       VARCHAR(50)  NOT NULL,
    conversion_rate DECIMAL(8,2)  NOT NULL CHECK (conversion_rate > 0),
    is_base_unit    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pu_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_product_unit_name UNIQUE (product_id, unit_name)
);

COMMENT ON TABLE  ProductUnits IS 'Đơn vị tính quy đổi. Mỗi product có đúng 1 row is_base_unit=TRUE';
COMMENT ON COLUMN ProductUnits.conversion_rate IS 'Số đơn vị cơ sở trong 1 đơn vị này. VD: 1 Thùng = 24 Lon thì conversion_rate=24';

CREATE INDEX idx_pu_product ON ProductUnits(product_id);

-- 15. ProductPriceHistory (Lịch sử giá)
-- UC1, UC8: Dashboard, Manage Products
CREATE TABLE ProductPriceHistory (
    id             SERIAL       PRIMARY KEY,
    product_id     INT            NOT NULL,
    unit_id        INT            NOT NULL,
    cost_price     DECIMAL(10,2)  NOT NULL CHECK (cost_price >= 0),
    sale_price     DECIMAL(10,2)  NOT NULL CHECK (sale_price >= 0),
    effective_date DATE           NOT NULL,
    created_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pph_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_pph_unit
        FOREIGN KEY (unit_id) REFERENCES ProductUnits(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE ProductPriceHistory IS 'Lịch sử giá theo đơn vị. Query giá hiện tại: ORDER BY effective_date DESC LIMIT 1';

CREATE INDEX idx_price_lookup ON ProductPriceHistory(product_id, unit_id, effective_date DESC);

-- ============================================================
-- BƯỚC 4: NHÓM BẢNG CHỨNG TỪ CHA & TỒN KHO (Header)
-- ============================================================

-- 16. Inventory (Tồn kho vật lý)
-- UC1, UC4, UC6, UC9, UC10
CREATE TABLE Inventory (
    id           SERIAL       PRIMARY KEY,
    product_id   INT            NOT NULL,
    location_id  INT            NOT NULL,
    batch_number VARCHAR(100),
    expiry_date  DATE,
    quantity     INT            NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_quantity INT            NOT NULL DEFAULT 0,
    updated_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_inv_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_inv_location
        FOREIGN KEY (location_id) REFERENCES WarehouseLocations(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_inventory_product_location_batch
        UNIQUE (product_id, location_id, batch_number)
);

COMMENT ON TABLE  Inventory IS 'Tồn kho vật lý. quantity luôn theo đơn vị cơ sở (base unit)';
COMMENT ON COLUMN Inventory.min_quantity IS 'Mức tối thiểu. Dưới mức này sẽ kích hoạt cảnh báo LowStock';

CREATE INDEX idx_inv_product     ON Inventory(product_id);
CREATE INDEX idx_inv_expiry_date ON Inventory(expiry_date);

-- 17. StockReceipts (Phiếu Nhập kho)
-- UC4, UC7, UC12
CREATE TABLE StockReceipts (
    id             SERIAL         PRIMARY KEY,
    receipt_code   VARCHAR(50)    NOT NULL UNIQUE,
    supplier_id    INT            NOT NULL,
    staff_id       INT            NOT NULL,
    receipt_date   DATE           NOT NULL,
    status         VARCHAR(20)    NOT NULL DEFAULT 'Draft'
                                  CHECK (status IN ('Draft', 'Pending', 'Approved', 'Rejected')),
    invoice_number VARCHAR(100),
    total_amount   DECIMAL(10,2)  NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    notes          TEXT,
    approved_by    INT,
    approved_at    TIMESTAMP,
    created_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sr_supplier
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_sr_staff
        FOREIGN KEY (staff_id) REFERENCES Users(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_sr_approver
        FOREIGN KEY (approved_by) REFERENCES Users(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE  StockReceipts IS 'Phiếu nhập kho. Chỉ khi status=Approved mới cộng vào Inventory và ghi FinanceLedger. VD: PN-2026-0001';
COMMENT ON COLUMN StockReceipts.approved_by IS 'Người duyệt (khi status=Approved)';

CREATE INDEX idx_sr_supplier ON StockReceipts(supplier_id);
CREATE INDEX idx_sr_status   ON StockReceipts(status);

-- 18. SalesOrders (Đơn hàng bán)
-- UC1, UC4, UC9, UC10
CREATE TABLE SalesOrders (
    id               SERIAL         PRIMARY KEY,
    order_code       VARCHAR(50)    NOT NULL UNIQUE,
    customer_id      INT            NOT NULL,
    user_id          INT            NOT NULL,
    total_amount     DECIMAL(10,2)  NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    discount_amount  DECIMAL(10,2)  NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    final_amount     DECIMAL(10,2)  GENERATED ALWAYS AS (total_amount - discount_amount) STORED,
    status           VARCHAR(20)    NOT NULL DEFAULT 'Pending'
                                    CHECK (status IN ('Pending', 'Processing', 'Partial', 'Shipped', 'Delivered', 'Cancelled')),
    parent_order_id  INT,
    shipping_address TEXT,
    notes            TEXT,
    created_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at     TIMESTAMP,
    cancelled_by     INT,
    -- Task054 / API_PROJECT_DESIGN §4.10 — UC9 list & kênh bán
    order_channel    VARCHAR(20)    NOT NULL DEFAULT 'Wholesale'
                                    CHECK (order_channel IN ('Retail', 'Wholesale', 'Return')),
    payment_status   VARCHAR(20)    NOT NULL DEFAULT 'Unpaid'
                                    CHECK (payment_status IN ('Paid', 'Unpaid', 'Partial')),
    ref_sales_order_id INT,

    CONSTRAINT fk_so_customer
        FOREIGN KEY (customer_id) REFERENCES Customers(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_so_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_so_parent
        FOREIGN KEY (parent_order_id) REFERENCES SalesOrders(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_so_cancelled_by
        FOREIGN KEY (cancelled_by) REFERENCES Users(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_so_ref_sales_order
        FOREIGN KEY (ref_sales_order_id) REFERENCES SalesOrders(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE  SalesOrders IS 'Đơn hàng bán. Backorder: đơn con trỏ parent_order_id về đơn cha. VD: SO-2026-0001';
COMMENT ON COLUMN SalesOrders.final_amount IS 'Cột tự động tính: total_amount - discount_amount';

CREATE INDEX idx_so_customer   ON SalesOrders(customer_id);
CREATE INDEX idx_so_user       ON SalesOrders(user_id);
CREATE INDEX idx_so_status     ON SalesOrders(status);
CREATE INDEX idx_so_parent     ON SalesOrders(parent_order_id);
CREATE INDEX idx_so_created_at ON SalesOrders(created_at);
CREATE INDEX idx_so_order_channel   ON SalesOrders(order_channel);
CREATE INDEX idx_so_payment_status  ON SalesOrders(payment_status);

-- ============================================================
-- BƯỚC 5: NHÓM BẢNG CHI TIẾT CHỨNG TỪ (Details)
-- ============================================================

-- 19. StockReceiptDetails (Chi tiết Phiếu Nhập)
-- UC7, UC12
CREATE TABLE StockReceiptDetails (
    id           SERIAL       PRIMARY KEY,
    receipt_id   INT            NOT NULL,
    product_id   INT            NOT NULL,
    unit_id      INT            NOT NULL,
    quantity     INT            NOT NULL CHECK (quantity > 0),
    cost_price   DECIMAL(10,2)  NOT NULL CHECK (cost_price >= 0),
    batch_number VARCHAR(100),
    expiry_date  DATE,
    line_total   DECIMAL(10,2)  GENERATED ALWAYS AS (quantity * cost_price) STORED,
    created_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_srd_receipt
        FOREIGN KEY (receipt_id) REFERENCES StockReceipts(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_srd_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_srd_unit
        FOREIGN KEY (unit_id) REFERENCES ProductUnits(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_srd_receipt_product_batch
        UNIQUE (receipt_id, product_id, batch_number)
);

COMMENT ON TABLE  StockReceiptDetails IS 'Chi tiết phiếu nhập kho. line_total tự động tính = quantity × cost_price';
COMMENT ON COLUMN StockReceiptDetails.line_total IS 'Generated Column: quantity * cost_price';

CREATE INDEX idx_srd_receipt ON StockReceiptDetails(receipt_id);

-- 20. OrderDetails (Chi tiết Đơn hàng)
-- UC9, UC10
CREATE TABLE OrderDetails (
    id              SERIAL       PRIMARY KEY,
    order_id        INT            NOT NULL,
    product_id      INT            NOT NULL,
    unit_id         INT            NOT NULL,
    quantity        INT            NOT NULL CHECK (quantity > 0),
    price_at_time   DECIMAL(10,2)  NOT NULL CHECK (price_at_time >= 0),
    line_total      DECIMAL(10,2)  GENERATED ALWAYS AS (quantity * price_at_time) STORED,
    dispatched_qty  INT            NOT NULL DEFAULT 0 CHECK (dispatched_qty >= 0),
    created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_od_order
        FOREIGN KEY (order_id) REFERENCES SalesOrders(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_od_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_od_unit
        FOREIGN KEY (unit_id) REFERENCES ProductUnits(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_od_order_product_unit
        UNIQUE (order_id, product_id, unit_id),

    CONSTRAINT chk_dispatched_qty
        CHECK (dispatched_qty <= quantity)
);

COMMENT ON TABLE  OrderDetails IS 'Chi tiết đơn hàng. line_total tự động tính. price_at_time không đổi khi giá thay đổi';
COMMENT ON COLUMN OrderDetails.dispatched_qty IS 'Số lượng đã xuất kho. dispatched_qty = quantity → đủ, < quantity → cần backorder';
COMMENT ON COLUMN OrderDetails.line_total IS 'Generated Column: quantity * price_at_time';

CREATE INDEX idx_od_order ON OrderDetails(order_id);

-- 21. StockDispatches (Phiếu Xuất kho)
-- UC4, UC10
CREATE TABLE StockDispatches (
    id             SERIAL       PRIMARY KEY,
    dispatch_code  VARCHAR(50)  NOT NULL UNIQUE,
    order_id       INT          NOT NULL,
    user_id        INT          NOT NULL,
    dispatch_date  DATE         NOT NULL,
    status         VARCHAR(20)  NOT NULL DEFAULT 'Pending'
                                CHECK (status IN ('Pending', 'Full', 'Partial', 'Cancelled')),
    notes          TEXT,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sd_order
        FOREIGN KEY (order_id) REFERENCES SalesOrders(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_sd_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE RESTRICT
);

COMMENT ON TABLE StockDispatches IS 'Phiếu xuất kho. 1 StockDispatches → N InventoryLogs. VD: PX-2026-0001';

CREATE INDEX idx_sd_order  ON StockDispatches(order_id);
CREATE INDEX idx_sd_status ON StockDispatches(status);

-- ============================================================
-- BƯỚC 6: BẢNG LOG CUỐI CÙNG (Phụ thuộc cao nhất)
-- ============================================================

-- 22. InventoryLogs (Nhật ký biến động Kho)
-- UC6, UC10: Manage inventory, Dispatch
CREATE TABLE InventoryLogs (
    id               SERIAL       PRIMARY KEY,
    product_id       INT            NOT NULL,
    action_type      VARCHAR(20)    NOT NULL
                                    CHECK (action_type IN ('INBOUND', 'OUTBOUND', 'TRANSFER', 'ADJUSTMENT')),
    quantity_change  INT            NOT NULL,
    unit_id          INT            NOT NULL,
    user_id          INT,
    dispatch_id      INT,
    receipt_id       INT,
    from_location_id INT,
    to_location_id   INT,
    reference_note   VARCHAR(255),
    created_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_il_product
        FOREIGN KEY (product_id) REFERENCES Products(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_il_unit
        FOREIGN KEY (unit_id) REFERENCES ProductUnits(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_il_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_il_dispatch
        FOREIGN KEY (dispatch_id) REFERENCES StockDispatches(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_il_receipt
        FOREIGN KEY (receipt_id) REFERENCES StockReceipts(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_il_from_location
        FOREIGN KEY (from_location_id) REFERENCES WarehouseLocations(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_il_to_location
        FOREIGN KEY (to_location_id) REFERENCES WarehouseLocations(id)
        ON DELETE SET NULL
);

COMMENT ON TABLE  InventoryLogs IS 'Nhật ký biến động kho. INBOUND(+), OUTBOUND(-), TRANSFER(from→to), ADJUSTMENT(+/-)';
COMMENT ON COLUMN InventoryLogs.quantity_change IS 'Dương (+) = nhập, Âm (-) = xuất';

CREATE INDEX idx_il_product    ON InventoryLogs(product_id);
CREATE INDEX idx_il_created_at ON InventoryLogs(created_at);
CREATE INDEX idx_il_dispatch   ON InventoryLogs(dispatch_id);
CREATE INDEX idx_il_receipt    ON InventoryLogs(receipt_id);

-- ============================================================
-- BẢNG OPTIONAL (Khuyến nghị từ UseCase_Database_Coverage.md)
-- ============================================================

-- 23. Notifications (Quản lý thông báo) [OPTIONAL]
-- UC4 post-condition: "Nhân viên nhận được thông báo"
CREATE TABLE Notifications (
    id                SERIAL       PRIMARY KEY,
    user_id           INT          NOT NULL,
    notification_type VARCHAR(30)  NOT NULL
                                   CHECK (notification_type IN ('ApprovalResult', 'LowStock', 'ExpiryWarning', 'SystemAlert')),
    title             VARCHAR(255) NOT NULL,
    message           TEXT         NOT NULL,
    is_read           BOOLEAN      NOT NULL DEFAULT FALSE,
    reference_type    VARCHAR(50),
    reference_id      INT,
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at           TIMESTAMP,

    CONSTRAINT fk_notif_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE Notifications IS '[OPTIONAL] Quản lý thông báo in-app. Phục vụ UC4 approval workflow';

CREATE INDEX idx_notif_user_unread ON Notifications(user_id, is_read);

-- ============================================================
-- BỔ SUNG 5.2: API / Database_Specification (StoreProfiles, thu chi, nợ, reset mật khẩu, kiểm kê)
-- ============================================================

-- StoreProfiles — §6.1 Database_Specification; API Task073/074/075
CREATE TABLE StoreProfiles (
    id                 SERIAL       PRIMARY KEY,
    owner_id           INT          NOT NULL UNIQUE,
    name               VARCHAR(255) NOT NULL,
    business_category  VARCHAR(255),
    address            TEXT,
    phone              VARCHAR(30),
    email              VARCHAR(255),
    website            VARCHAR(500),
    tax_code           VARCHAR(50),
    footer_note        TEXT,
    logo_url           VARCHAR(500),
    facebook_url       VARCHAR(500),
    instagram_handle   VARCHAR(255),
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_store_profiles_owner
        FOREIGN KEY (owner_id) REFERENCES Users(id)
        ON DELETE CASCADE
);

COMMENT ON TABLE StoreProfiles IS 'Hồ sơ cửa hàng theo Owner; logo/MST cho hóa đơn & POS';

CREATE INDEX idx_store_profiles_owner ON StoreProfiles(owner_id);

-- CashTransactions — §12.1; API Task064–068
CREATE TABLE CashTransactions (
    id                 SERIAL          PRIMARY KEY,
    transaction_code   VARCHAR(50)     NOT NULL UNIQUE,
    direction          VARCHAR(10)     NOT NULL
                                       CHECK (direction IN ('Income', 'Expense')),
    amount             DECIMAL(15,2)   NOT NULL CHECK (amount > 0),
    category           VARCHAR(100)    NOT NULL,
    description        TEXT,
    payment_method     VARCHAR(30)     NOT NULL DEFAULT 'Cash',
    status             VARCHAR(20)     NOT NULL DEFAULT 'Pending'
                                       CHECK (status IN ('Pending', 'Completed', 'Cancelled')),
    transaction_date   DATE            NOT NULL,
    finance_ledger_id  INT,
    created_by         INT             NOT NULL,
    created_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cash_tx_ledger
        FOREIGN KEY (finance_ledger_id) REFERENCES FinanceLedger(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_cash_tx_created_by
        FOREIGN KEY (created_by) REFERENCES Users(id)
        ON DELETE RESTRICT
);

COMMENT ON TABLE CashTransactions IS 'Thu/chi thủ công; khi Completed liên kết FinanceLedger';

CREATE INDEX idx_cash_tx_date   ON CashTransactions(transaction_date);
CREATE INDEX idx_cash_tx_status ON CashTransactions(status);

-- PartnerDebts — §12.2; API Task069–072
CREATE TABLE PartnerDebts (
    id             SERIAL          PRIMARY KEY,
    debt_code      VARCHAR(50)     NOT NULL UNIQUE,
    partner_type   VARCHAR(20)     NOT NULL
                                   CHECK (partner_type IN ('Customer', 'Supplier')),
    customer_id    INT,
    supplier_id    INT,
    total_amount   DECIMAL(15,2)   NOT NULL CHECK (total_amount >= 0),
    paid_amount    DECIMAL(15,2)   NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
    due_date       DATE,
    status         VARCHAR(20)     NOT NULL DEFAULT 'InDebt'
                                   CHECK (status IN ('InDebt', 'Cleared')),
    notes          TEXT,
    created_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pd_customer
        FOREIGN KEY (customer_id) REFERENCES Customers(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_pd_supplier
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_partner_debts_partner
        CHECK (
            (partner_type = 'Customer' AND customer_id IS NOT NULL AND supplier_id IS NULL)
            OR (partner_type = 'Supplier' AND supplier_id IS NOT NULL AND customer_id IS NULL)
        ),

    CONSTRAINT chk_paid_le_total
        CHECK (paid_amount <= total_amount)
);

COMMENT ON TABLE PartnerDebts IS 'Sổ nợ KH/NCC; remaining = total_amount - paid_amount (API)';

CREATE INDEX idx_partner_debts_status   ON PartnerDebts(status);
CREATE INDEX idx_partner_debts_customer ON PartnerDebts(customer_id);
CREATE INDEX idx_partner_debts_supplier ON PartnerDebts(supplier_id);

-- StaffPasswordResetRequests — API Task004 §4
CREATE TABLE StaffPasswordResetRequests (
    id            SERIAL       PRIMARY KEY,
    user_id       INT          NOT NULL,
    message       TEXT,
    status        VARCHAR(20)  NOT NULL DEFAULT 'Pending'
                             CHECK (status IN ('Pending', 'Processed', 'Cancelled')),
    processed_by  INT,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at  TIMESTAMP,

    CONSTRAINT fk_sp_reset_user
        FOREIGN KEY (user_id) REFERENCES Users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_sp_reset_processor
        FOREIGN KEY (processed_by) REFERENCES Users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_sp_reset_user_status ON StaffPasswordResetRequests(user_id, status);

-- Inventory audit — API Task021–028 (DDL Task022 + idempotency Task028)
CREATE TABLE InventoryAuditSessions (
    id               SERIAL       PRIMARY KEY,
    audit_code       VARCHAR(50)  NOT NULL UNIQUE,
    title            VARCHAR(255) NOT NULL,
    audit_date       DATE         NOT NULL,
    status           VARCHAR(20)  NOT NULL
                                CHECK (status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
    location_filter  VARCHAR(100),
    category_filter  VARCHAR(50),
    notes            TEXT,
    created_by       INT          NOT NULL,
    completed_at     TIMESTAMP,
    completed_by     INT,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_session_creator
        FOREIGN KEY (created_by) REFERENCES Users(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_audit_session_completer
        FOREIGN KEY (completed_by) REFERENCES Users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_audit_sessions_status ON InventoryAuditSessions(status);

CREATE TABLE InventoryAuditLines (
    id                   SERIAL       PRIMARY KEY,
    session_id           INT          NOT NULL,
    inventory_id         INT          NOT NULL,
    system_quantity      DECIMAL(12, 4) NOT NULL,
    actual_quantity      DECIMAL(12, 4),
    is_counted           BOOLEAN      NOT NULL DEFAULT FALSE,
    notes                VARCHAR(500),
    variance_applied_at  TIMESTAMP,
    created_at           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_line_session
        FOREIGN KEY (session_id) REFERENCES InventoryAuditSessions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_audit_line_inventory
        FOREIGN KEY (inventory_id) REFERENCES Inventory(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_audit_lines_session ON InventoryAuditLines(session_id);

-- ============================================================
-- TRIGGER: Tự động cập nhật updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Áp dụng trigger cho các bảng có cột updated_at
CREATE TRIGGER trg_categories_updated    BEFORE UPDATE ON Categories         FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_suppliers_updated     BEFORE UPDATE ON Suppliers          FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_customers_updated     BEFORE UPDATE ON Customers          FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_users_updated         BEFORE UPDATE ON Users              FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_products_updated      BEFORE UPDATE ON Products           FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_alertsettings_updated BEFORE UPDATE ON AlertSettings      FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_finance_updated       BEFORE UPDATE ON FinanceLedger      FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_productunits_updated  BEFORE UPDATE ON ProductUnits       FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_inventory_updated     BEFORE UPDATE ON Inventory          FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_stockreceipts_updated BEFORE UPDATE ON StockReceipts      FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_salesorders_updated   BEFORE UPDATE ON SalesOrders        FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_dispatches_updated    BEFORE UPDATE ON StockDispatches    FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_storeprofiles_updated BEFORE UPDATE ON StoreProfiles      FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_cashtx_updated        BEFORE UPDATE ON CashTransactions   FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_partnerdebts_updated  BEFORE UPDATE ON PartnerDebts       FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_audit_sessions_updated BEFORE UPDATE ON InventoryAuditSessions FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();
CREATE TRIGGER trg_audit_lines_updated    BEFORE UPDATE ON InventoryAuditLines    FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

-- ============================================================
-- SEED DATA: Dữ liệu khởi tạo để chạy dự án
-- ============================================================

-- Roles mặc định
INSERT INTO Roles (name, permissions) VALUES
('Owner', '{"can_view_dashboard": true, "can_manage_staff": true, "can_approve": true, "can_configure_alerts": true, "can_view_finance": true, "can_manage_products": true, "can_manage_inventory": true, "can_manage_orders": true, "can_use_ai": true}'),
('Staff', '{"can_view_dashboard": false, "can_manage_staff": false, "can_approve": false, "can_configure_alerts": false, "can_view_finance": false, "can_manage_products": true, "can_manage_inventory": true, "can_manage_orders": true, "can_use_ai": true}'),
('Admin', '{"can_view_dashboard": true, "can_manage_staff": true, "can_approve": true, "can_configure_alerts": true, "can_view_finance": true, "can_manage_products": true, "can_manage_inventory": true, "can_manage_orders": true, "can_use_ai": true}');

-- User Admin mặc định (password: admin123 → cần hash thực tế khi deploy)
-- Mật khẩu dev mặc định: Admin@123 (bcrypt cập nhật bởi Flyway backend V2 khi chạy PostgreSQL).
INSERT INTO Users (username, password_hash, full_name, email, role_id, status) VALUES
('admin', '$2a$10$placeholder_hash_replace_in_production', 'System Administrator', 'admin@smartinventory.vn', 1, 'Active');

-- Vị trí kho mẫu
INSERT INTO WarehouseLocations (warehouse_code, shelf_code, description) VALUES
('WH01', 'A1', 'Kệ A1 - Kho chính - Hàng khô'),
('WH01', 'A2', 'Kệ A2 - Kho chính - Hàng khô'),
('WH01', 'B1', 'Kệ B1 - Kho chính - Hàng lạnh'),
('WH01', 'B2', 'Kệ B2 - Kho chính - Hàng lạnh'),
('WH01', 'C1', 'Kệ C1 - Kho chính - Hàng nặng');

-- Danh mục mẫu
INSERT INTO Categories (category_code, name, description, sort_order) VALUES
('CAT001', 'Thực phẩm khô',     'Mì, gạo, bột, gia vị',       1),
('CAT002', 'Đồ uống',           'Nước ngọt, sữa, nước suối',   2),
('CAT003', 'Hóa phẩm',          'Xà phòng, nước rửa chén',     3),
('CAT004', 'Đồ dùng gia đình',  'Chổi, khăn, giấy vệ sinh',   4);

-- ============================================================
-- HOÀN TẤT
-- ============================================================
-- Tổng: 29 bảng (23 chính + 1 optional Notifications + 5 bổ sung 5.2)
-- Foreign Keys: 43+
-- UNIQUE Constraints: 14+
-- CHECK Constraints: 18+
-- Indexes: 32+
-- Generated Columns: 3 (line_total x2, final_amount x1)
-- Triggers: 12 (auto-update updated_at)
-- Seed Data: Roles, Users, WarehouseLocations, Categories
--
-- ĐÃ TỐI GIẢN CHO ĐỒ ÁN NHỎ:
-- - SERIAL thay BIGSERIAL (đủ cho 2.1 tỷ rows)
-- - INT thay DECIMAL cho quantity (số nguyên là đủ)
-- - DECIMAL(10,2) thay DECIMAL(15,2) (999 tỷ là đủ)
-- - Thêm bảng ProductImages cho UC8, UC12
-- ============================================================
