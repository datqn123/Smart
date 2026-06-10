# Seed Data — Sản phẩm & Danh mục thực tế

> Mục đích: thay thế 50 sản phẩm chung chung "Hàng seed demo #N" (V8) bằng sản phẩm có tên thật, phục vụ demo, testing, và AI training.
>
> **Phạm vi:** Categories, Products, ProductUnits, ProductPriceHistory  
> **Không đụng:** Inventory, StockReceipts, StockDispatches, SalesOrders

---

## 1. Danh mục đích (Categories)

Sử dụng **categories đã seed từ V1, V6, V16** — không tạo mới. Chỉ map `category_id` vào các danh mục sau:

| Mã DM | Tên DM | Gốc? | Ghi chú |
|-------|--------|------|---------|
| `CAT001` | Thực phẩm khô | Gốc (V1) | |
| `CAT002` | Đồ uống | Gốc (V1) | |
| `CAT003` | Hóa phẩm | Gốc (V1) | |
| `CAT004` | Đồ dùng gia đình | Gốc (V1) | |
| `CAT005` | Bánh kẹo | Gốc (V6) | |
| `CAT006` | Gia vị | Gốc (V6) | |
| `DM50_020` | Sữa tươi & UHT | Gốc (V16) | |
| `DM50_021` | Sữa chua & Phomat | Gốc (V16) | |
| `DM50_022` | Bia & Rượu | Gốc (V16) | |
| `DM50_023` | Nước ngọt | Gốc (V16) | |
| `DM50_025` | Trà & Cà phê hòa tan | Gốc (V16) | |
| `DM50_050` | Mỹ phẩm & Chăm sóc cá nhân | Gốc (V16) | |

> **Lưu ý:** Vì `category_id` là FK với `ON DELETE SET NULL`, join bằng `category_code` để tránh phụ thuộc ID cứng.

---

## 2. Danh sách sản phẩm (72 SP)

### 2.1 Thực phẩm khô — CAT001 (~15 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 1 | SP-TP-001 | Mì Hảo Hảo tôm chua cay 75g | 200001000001 | 75 | 3,200 | 4,500 |
| 2 | SP-TP-002 | Mì Hảo Hảo sườn heo 75g | 200001000002 | 75 | 3,200 | 4,500 |
| 3 | SP-TP-003 | Mì Gấu Đỏ tôm cay 80g | 200001000003 | 80 | 3,000 | 4,200 |
| 4 | SP-TP-004 | Mì Omachi xào chua ngọt 85g | 200001000004 | 85 | 4,000 | 5,500 |
| 5 | SP-TP-005 | Gạo ST25 túi 5kg | 200001000005 | 5000 | 85,000 | 105,000 |
| 6 | SP-TP-006 | Gạo Nàng Hương túi 5kg | 200001000006 | 5000 | 72,000 | 90,000 |
| 7 | SP-TP-007 | Bún khô 500g | 200001000007 | 500 | 12,000 | 17,000 |
| 8 | SP-TP-008 | Miến dong 500g | 200001000008 | 500 | 18,000 | 25,000 |
| 9 | SP-TP-009 | Nui vỏ sò 500g | 200001000009 | 500 | 14,000 | 20,000 |
| 10 | SP-TP-010 | Bột mì đa dụng Bakers Choice 1kg | 200001000010 | 1000 | 18,000 | 25,000 |
| 11 | SP-TP-011 | Bột chiên giòn 500g | 200001000011 | 500 | 10,000 | 15,000 |
| 12 | SP-TP-012 | Yến mạch nguyên hạt 1kg | 200001000012 | 1000 | 35,000 | 48,000 |
| 13 | SP-TP-013 | Đậu xanh tách vỏ 1kg | 200001000013 | 1000 | 28,000 | 38,000 |
| 14 | SP-TP-014 | Đậu đen 1kg | 200001000014 | 1000 | 25,000 | 35,000 |
| 15 | SP-TP-015 | Bắp rang bơ lò vi sóng 100g | 200001000015 | 100 | 8,000 | 12,000 |

### 2.2 Đồ uống — CAT002 (~8 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 16 | SP-DU-001 | Nước suối Aquafina 500ml | 200002000001 | 500 | 3,000 | 5,000 |
| 17 | SP-DU-002 | Nước suối Lavie 1.5L | 200002000002 | 1500 | 5,000 | 8,000 |
| 18 | SP-DU-003 | Trà xanh C2 hương chanh 500ml | 200002000003 | 500 | 4,500 | 7,000 |
| 19 | SP-DU-004 | Trà ô long Tea+ hương đào 500ml | 200002000004 | 500 | 5,000 | 8,000 |
| 20 | SP-DU-005 | Nước tăng lực Number 1 330ml | 200002000005 | 330 | 5,500 | 9,000 |
| 21 | SP-DU-006 | Nước tăng lực Red Bull 250ml | 200002000006 | 250 | 8,000 | 12,000 |
| 22 | SP-DU-007 | Cà phê đen đá lon 240ml | 200002000007 | 240 | 6,000 | 10,000 |
| 23 | SP-DU-008 | Nước dừa tươi Cocoxim 330ml | 200002000008 | 330 | 7,000 | 11,000 |

### 2.3 Hóa phẩm — CAT003 (~8 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 24 | SP-HP-001 | Nước rửa chén Sunlight chanh 750ml | 200003000001 | 750 | 18,000 | 26,000 |
| 25 | SP-HP-002 | Nước rửa chén Đại Việt hương táo 1L | 200003000002 | 1000 | 14,000 | 20,000 |
| 26 | SP-HP-003 | Bột giặt OMO Matic 2.5kg | 200003000003 | 2500 | 55,000 | 75,000 |
| 27 | SP-HP-004 | Bột giặt Tide thơm lâu 2kg | 200003000004 | 2000 | 48,000 | 65,000 |
| 28 | SP-HP-005 | Nước xả Comfort hồng 1.5L | 200003000005 | 1500 | 30,000 | 42,000 |
| 29 | SP-HP-006 | Nước lau sàn Jex 2L | 200003000006 | 2000 | 25,000 | 35,000 |
| 30 | SP-HP-007 | Thuốc tẩy Javen 1L | 200003000007 | 1000 | 8,000 | 12,000 |
| 31 | SP-HP-008 | Nước rửa tay Lifebuoy tinh khiết 500ml | 200003000008 | 500 | 15,000 | 22,000 |

### 2.4 Đồ dùng gia đình — CAT004 (~5 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 32 | SP-DD-001 | Khăn giấy ướt Bobby 30 tờ | 200004000001 | 100 | 6,000 | 10,000 |
| 33 | SP-DD-002 | Giấy vệ sinh Pulppy cuộn 4 cuộn | 200004000002 | 400 | 12,000 | 18,000 |
| 34 | SP-DD-003 | Khăn giấy ăn Pulppy 200 tờ | 200004000003 | 200 | 8,000 | 13,000 |
| 35 | SP-DD-004 | Túi rác đen 40x60cm 50 cái | 200004000004 | 500 | 12,000 | 18,000 |
| 36 | SP-DD-005 | Chổi quét nhà inox cán gỗ | 200004000005 | 600 | 20,000 | 30,000 |

### 2.5 Bánh kẹo — CAT005 (~10 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 37 | SP-BK-001 | Bánh quy Oreo vị socola 137g | 200005000001 | 137 | 18,000 | 25,000 |
| 38 | SP-BK-002 | Bánh Oreo vị dâu 137g | 200005000002 | 137 | 18,000 | 25,000 |
| 39 | SP-BK-003 | Bánh Cosy kem sữa 115g | 200005000003 | 115 | 9,000 | 14,000 |
| 40 | SP-BK-004 | Bánh AFC hương bơ 110g | 200005000004 | 110 | 8,000 | 12,000 |
| 41 | SP-BK-005 | Kẹo dẻo Haribo Goldbären 100g | 200005000005 | 100 | 15,000 | 22,000 |
| 42 | SP-BK-006 | Kẹo sữa Kopiko 100g | 200005000006 | 100 | 12,000 | 18,000 |
| 43 | SP-BK-007 | Snack Poca vị bò nướng BBQ 85g | 200005000007 | 85 | 10,000 | 15,000 |
| 44 | SP-BK-008 | Snack O'Star tôm cay 80g | 200005000008 | 80 | 8,000 | 12,000 |
| 45 | SP-BK-009 | Bim Bim Lays vị tự nhiên 90g | 200005000009 | 90 | 10,000 | 15,000 |
| 46 | SP-BK-010 | Bánh Chocopie hộp 12 cái 408g | 200005000010 | 408 | 28,000 | 38,000 |

### 2.6 Gia vị — CAT006 (~8 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 47 | SP-GV-001 | Nước mắm Nam Ngư đệ nhị 500ml | 200006000001 | 500 | 20,000 | 32,000 |
| 48 | SP-GV-002 | Nước mắm Chin-su cá cơm 500ml | 200006000002 | 500 | 25,000 | 38,000 |
| 49 | SP-GV-003 | Dầu ăn Neptune 1L | 200006000003 | 1000 | 28,000 | 38,000 |
| 50 | SP-GV-004 | Dầu ăn Tường An 1L | 200006000004 | 1000 | 25,000 | 35,000 |
| 51 | SP-GV-005 | Hạt nêm Knorr gà 900g | 200006000005 | 900 | 30,000 | 42,000 |
| 52 | SP-GV-006 | Bột ngọt Ajinomoto 200g | 200006000006 | 200 | 8,000 | 12,000 |
| 53 | SP-GV-007 | Đường cát trắng Biên Hòa 1kg | 200006000007 | 1000 | 15,000 | 22,000 |
| 54 | SP-GV-008 | Muối tinh 500g | 200006000008 | 500 | 3,000 | 5,000 |

### 2.7 Sữa & Chế phẩm từ sữa — DM50_020 + DM50_021 (~8 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 55 | SP-SU-001 | Sữa tươi tiệt trùng Vinamilk 1L | 200020000001 | 1000 | 22,000 | 30,000 |
| 56 | SP-SU-002 | Sữa tươi tiệt trùng TH True Milk 1L | 200020000002 | 1000 | 24,000 | 32,000 |
| 57 | SP-SU-003 | Sữa đặc Ông Thọ hộp 380g | 200020000003 | 380 | 18,000 | 25,000 |
| 58 | SP-SU-004 | Sữa hộp Milo 180ml | 200020000004 | 180 | 5,000 | 8,000 |
| 59 | SP-SU-005 | Sữa chua Vinamilk hũ trắng 100g | 200021000001 | 100 | 3,000 | 5,000 |
| 60 | SP-SU-006 | Sữa chua Đà Lạt sữa đặc 120g | 200021000002 | 120 | 3,500 | 6,000 |
| 61 | SP-SU-007 | Phô mai con bò cười viên 120g | 200021000003 | 120 | 16,000 | 22,000 |
| 62 | SP-SU-008 | Trang trại sữa chua uống Probi 220ml | 200021000004 | 220 | 6,000 | 10,000 |

### 2.8 Bia & Nước ngọt — DM50_022 + DM50_023 (~5 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 63 | SP-NN-001 | Coca-Cola 330ml lon | 200022000001 | 330 | 5,000 | 8,000 |
| 64 | SP-NN-002 | Pepsi 330ml lon | 200022000002 | 330 | 5,000 | 8,000 |
| 65 | SP-NN-003 | Bia Tiger bạc 330ml lon | 200022000003 | 330 | 8,000 | 12,000 |
| 66 | SP-NN-004 | Bia Heineken 330ml lon | 200022000004 | 330 | 10,000 | 15,000 |
| 67 | SP-NN-005 | Bia Sài Gòn đỏ 330ml lon | 200022000005 | 330 | 6,000 | 10,000 |

### 2.9 Chăm sóc cá nhân — DM50_050 (~5 SP)

| # | SKU | Tên sản phẩm | Barcode | Weight (g) | Giá vốn | Giá bán |
|---|-----|-------------|---------|-----------|---------|---------|
| 68 | SP-CS-001 | Dầu gội Clear nam 350ml | 200050000001 | 350 | 28,000 | 40,000 |
| 69 | SP-CS-002 | Dầu gội Sunsilk mềm mượt 350ml | 200050000002 | 350 | 28,000 | 40,000 |
| 70 | SP-CS-003 | Sữa tắm Lifebuoy diệt khuẩn 500ml | 200050000003 | 500 | 25,000 | 36,000 |
| 71 | SP-CS-004 | Kem đánh răng P/S bảo vệ men 180g | 200050000004 | 180 | 12,000 | 18,000 |
| 72 | SP-CS-005 | Lăn khử mùi Nivea Black & White 50ml | 200050000005 | 50 | 22,000 | 32,000 |

---

## 3. SQL INSERT Script

### 3.1 Insert Products

```sql
-- ============================================================
-- SEED 72 SẢN PHẨM THỰC TẾ
-- Chạy sau khi Flyway V16 đã seed xong categories.
-- ============================================================

DO $$
DECLARE
    v_cat_id INT;
BEGIN

    -- 2.1 Thực phẩm khô — CAT001
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'CAT001' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-TP-001', '200001000001', 'Mì Hảo Hảo tôm chua cay 75g', 75, 'Active'),
        (v_cat_id, 'SP-TP-002', '200001000002', 'Mì Hảo Hảo sườn heo 75g', 75, 'Active'),
        (v_cat_id, 'SP-TP-003', '200001000003', 'Mì Gấu Đỏ tôm cay 80g', 80, 'Active'),
        (v_cat_id, 'SP-TP-004', '200001000004', 'Mì Omachi xào chua ngọt 85g', 85, 'Active'),
        (v_cat_id, 'SP-TP-005', '200001000005', 'Gạo ST25 túi 5kg', 5000, 'Active'),
        (v_cat_id, 'SP-TP-006', '200001000006', 'Gạo Nàng Hương túi 5kg', 5000, 'Active'),
        (v_cat_id, 'SP-TP-007', '200001000007', 'Bún khô 500g', 500, 'Active'),
        (v_cat_id, 'SP-TP-008', '200001000008', 'Miến dong 500g', 500, 'Active'),
        (v_cat_id, 'SP-TP-009', '200001000009', 'Nui vỏ sò 500g', 500, 'Active'),
        (v_cat_id, 'SP-TP-010', '200001000010', 'Bột mì đa dụng Bakers Choice 1kg', 1000, 'Active'),
        (v_cat_id, 'SP-TP-011', '200001000011', 'Bột chiên giòn 500g', 500, 'Active'),
        (v_cat_id, 'SP-TP-012', '200001000012', 'Yến mạch nguyên hạt 1kg', 1000, 'Active'),
        (v_cat_id, 'SP-TP-013', '200001000013', 'Đậu xanh tách vỏ 1kg', 1000, 'Active'),
        (v_cat_id, 'SP-TP-014', '200001000014', 'Đậu đen 1kg', 1000, 'Active'),
        (v_cat_id, 'SP-TP-015', '200001000015', 'Bắp rang bơ lò vi sóng 100g', 100, 'Active');

    -- 2.2 Đồ uống — CAT002
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'CAT002' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-DU-001', '200002000001', 'Nước suối Aquafina 500ml', 500, 'Active'),
        (v_cat_id, 'SP-DU-002', '200002000002', 'Nước suối Lavie 1.5L', 1500, 'Active'),
        (v_cat_id, 'SP-DU-003', '200002000003', 'Trà xanh C2 hương chanh 500ml', 500, 'Active'),
        (v_cat_id, 'SP-DU-004', '200002000004', 'Trà ô long Tea+ hương đào 500ml', 500, 'Active'),
        (v_cat_id, 'SP-DU-005', '200002000005', 'Nước tăng lực Number 1 330ml', 330, 'Active'),
        (v_cat_id, 'SP-DU-006', '200002000006', 'Nước tăng lực Red Bull 250ml', 250, 'Active'),
        (v_cat_id, 'SP-DU-007', '200002000007', 'Cà phê đen đá lon 240ml', 240, 'Active'),
        (v_cat_id, 'SP-DU-008', '200002000008', 'Nước dừa tươi Cocoxim 330ml', 330, 'Active');

    -- 2.3 Hóa phẩm — CAT003
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'CAT003' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-HP-001', '200003000001', 'Nước rửa chén Sunlight chanh 750ml', 750, 'Active'),
        (v_cat_id, 'SP-HP-002', '200003000002', 'Nước rửa chén Đại Việt hương táo 1L', 1000, 'Active'),
        (v_cat_id, 'SP-HP-003', '200003000003', 'Bột giặt OMO Matic 2.5kg', 2500, 'Active'),
        (v_cat_id, 'SP-HP-004', '200003000004', 'Bột giặt Tide thơm lâu 2kg', 2000, 'Active'),
        (v_cat_id, 'SP-HP-005', '200003000005', 'Nước xả Comfort hồng 1.5L', 1500, 'Active'),
        (v_cat_id, 'SP-HP-006', '200003000006', 'Nước lau sàn Jex 2L', 2000, 'Active'),
        (v_cat_id, 'SP-HP-007', '200003000007', 'Thuốc tẩy Javen 1L', 1000, 'Active'),
        (v_cat_id, 'SP-HP-008', '200003000008', 'Nước rửa tay Lifebuoy tinh khiết 500ml', 500, 'Active');

    -- 2.4 Đồ dùng gia đình — CAT004
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'CAT004' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-DD-001', '200004000001', 'Khăn giấy ướt Bobby 30 tờ', 100, 'Active'),
        (v_cat_id, 'SP-DD-002', '200004000002', 'Giấy vệ sinh Pulppy cuộn 4 cuộn', 400, 'Active'),
        (v_cat_id, 'SP-DD-003', '200004000003', 'Khăn giấy ăn Pulppy 200 tờ', 200, 'Active'),
        (v_cat_id, 'SP-DD-004', '200004000004', 'Túi rác đen 40x60cm 50 cái', 500, 'Active'),
        (v_cat_id, 'SP-DD-005', '200004000005', 'Chổi quét nhà inox cán gỗ', 600, 'Active');

    -- 2.5 Bánh kẹo — CAT005
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'CAT005' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-BK-001', '200005000001', 'Bánh quy Oreo vị socola 137g', 137, 'Active'),
        (v_cat_id, 'SP-BK-002', '200005000002', 'Bánh Oreo vị dâu 137g', 137, 'Active'),
        (v_cat_id, 'SP-BK-003', '200005000003', 'Bánh Cosy kem sữa 115g', 115, 'Active'),
        (v_cat_id, 'SP-BK-004', '200005000004', 'Bánh AFC hương bơ 110g', 110, 'Active'),
        (v_cat_id, 'SP-BK-005', '200005000005', 'Kẹo dẻo Haribo Goldbären 100g', 100, 'Active'),
        (v_cat_id, 'SP-BK-006', '200005000006', 'Kẹo sữa Kopiko 100g', 100, 'Active'),
        (v_cat_id, 'SP-BK-007', '200005000007', 'Snack Poca vị bò nướng BBQ 85g', 85, 'Active'),
        (v_cat_id, 'SP-BK-008', '200005000008', 'Snack O''Star tôm cay 80g', 80, 'Active'),
        (v_cat_id, 'SP-BK-009', '200005000009', 'Bim Bim Lays vị tự nhiên 90g', 90, 'Active'),
        (v_cat_id, 'SP-BK-010', '200005000010', 'Bánh Chocopie hộp 12 cái 408g', 408, 'Active');

    -- 2.6 Gia vị — CAT006
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'CAT006' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-GV-001', '200006000001', 'Nước mắm Nam Ngư đệ nhị 500ml', 500, 'Active'),
        (v_cat_id, 'SP-GV-002', '200006000002', 'Nước mắm Chin-su cá cơm 500ml', 500, 'Active'),
        (v_cat_id, 'SP-GV-003', '200006000003', 'Dầu ăn Neptune 1L', 1000, 'Active'),
        (v_cat_id, 'SP-GV-004', '200006000004', 'Dầu ăn Tường An 1L', 1000, 'Active'),
        (v_cat_id, 'SP-GV-005', '200006000005', 'Hạt nêm Knorr gà 900g', 900, 'Active'),
        (v_cat_id, 'SP-GV-006', '200006000006', 'Bột ngọt Ajinomoto 200g', 200, 'Active'),
        (v_cat_id, 'SP-GV-007', '200006000007', 'Đường cát trắng Biên Hòa 1kg', 1000, 'Active'),
        (v_cat_id, 'SP-GV-008', '200006000008', 'Muối tinh 500g', 500, 'Active');

    -- 2.7 Sữa & Chế phẩm — DM50_020 + DM50_021
    -- Sữa tươi
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'DM50_020' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-SU-001', '200020000001', 'Sữa tươi tiệt trùng Vinamilk 1L', 1000, 'Active'),
        (v_cat_id, 'SP-SU-002', '200020000002', 'Sữa tươi tiệt trùng TH True Milk 1L', 1000, 'Active'),
        (v_cat_id, 'SP-SU-003', '200020000003', 'Sữa đặc Ông Thọ hộp 380g', 380, 'Active'),
        (v_cat_id, 'SP-SU-004', '200020000004', 'Sữa hộp Milo 180ml', 180, 'Active');
    -- Sữa chua & Phomat
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'DM50_021' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-SU-005', '200021000001', 'Sữa chua Vinamilk hũ trắng 100g', 100, 'Active'),
        (v_cat_id, 'SP-SU-006', '200021000002', 'Sữa chua Đà Lạt sữa đặc 120g', 120, 'Active'),
        (v_cat_id, 'SP-SU-007', '200021000003', 'Phô mai con bò cười viên 120g', 120, 'Active'),
        (v_cat_id, 'SP-SU-008', '200021000004', 'Trang trại sữa chua uống Probi 220ml', 220, 'Active');

    -- 2.8 Bia & Nước ngọt — DM50_022 + DM50_023
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'DM50_022' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-NN-001', '200022000001', 'Coca-Cola 330ml lon', 330, 'Active'),
        (v_cat_id, 'SP-NN-002', '200022000002', 'Pepsi 330ml lon', 330, 'Active'),
        (v_cat_id, 'SP-NN-003', '200022000003', 'Bia Tiger bạc 330ml lon', 330, 'Active'),
        (v_cat_id, 'SP-NN-004', '200022000004', 'Bia Heineken 330ml lon', 330, 'Active'),
        (v_cat_id, 'SP-NN-005', '200022000005', 'Bia Sài Gòn đỏ 330ml lon', 330, 'Active');

    -- 2.9 Chăm sóc cá nhân — DM50_050
    SELECT id INTO v_cat_id FROM categories WHERE category_code = 'DM50_050' AND deleted_at IS NULL;
    INSERT INTO products (category_id, sku_code, barcode, name, weight, status) VALUES
        (v_cat_id, 'SP-CS-001', '200050000001', 'Dầu gội Clear nam 350ml', 350, 'Active'),
        (v_cat_id, 'SP-CS-002', '200050000002', 'Dầu gội Sunsilk mềm mượt 350ml', 350, 'Active'),
        (v_cat_id, 'SP-CS-003', '200050000003', 'Sữa tắm Lifebuoy diệt khuẩn 500ml', 500, 'Active'),
        (v_cat_id, 'SP-CS-004', '200050000004', 'Kem đánh răng P/S bảo vệ men 180g', 180, 'Active'),
        (v_cat_id, 'SP-CS-005', '200050000005', 'Lăn khử mùi Nivea Black & White 50ml', 50, 'Active');

END $$;
```

### 3.2 Insert ProductUnits (Base Unit)

```sql
-- ============================================================
-- ĐƠN VỊ CƠ SỞ — mỗi sản phẩm đúng 1 dòng is_base_unit = TRUE
-- ============================================================

INSERT INTO productunits (product_id, unit_name, conversion_rate, is_base_unit)
SELECT p.id, u.unit_name, 1.0, TRUE
FROM products p
JOIN (VALUES
    -- Thực phẩm khô
    ('SP-TP-001', 'Gói'), ('SP-TP-002', 'Gói'), ('SP-TP-003', 'Gói'),
    ('SP-TP-004', 'Gói'), ('SP-TP-005', 'Túi'), ('SP-TP-006', 'Túi'),
    ('SP-TP-007', 'Gói'), ('SP-TP-008', 'Gói'), ('SP-TP-009', 'Gói'),
    ('SP-TP-010', 'Gói'), ('SP-TP-011', 'Gói'), ('SP-TP-012', 'Gói'),
    ('SP-TP-013', 'Gói'), ('SP-TP-014', 'Gói'), ('SP-TP-015', 'Gói'),
    -- Đồ uống
    ('SP-DU-001', 'Chai'), ('SP-DU-002', 'Chai'), ('SP-DU-003', 'Chai'),
    ('SP-DU-004', 'Chai'), ('SP-DU-005', 'Lon'), ('SP-DU-006', 'Lon'),
    ('SP-DU-007', 'Lon'), ('SP-DU-008', 'Chai'),
    -- Hóa phẩm
    ('SP-HP-001', 'Chai'), ('SP-HP-002', 'Chai'), ('SP-HP-003', 'Túi'),
    ('SP-HP-004', 'Túi'), ('SP-HP-005', 'Chai'), ('SP-HP-006', 'Chai'),
    ('SP-HP-007', 'Chai'), ('SP-HP-008', 'Chai'),
    -- Đồ gia dụng
    ('SP-DD-001', 'Gói'), ('SP-DD-002', 'Cuộn'), ('SP-DD-003', 'Hộp'),
    ('SP-DD-004', 'Cuộn'), ('SP-DD-005', 'Cây'),
    -- Bánh kẹo
    ('SP-BK-001', 'Hộp'), ('SP-BK-002', 'Hộp'), ('SP-BK-003', 'Hộp'),
    ('SP-BK-004', 'Hộp'), ('SP-BK-005', 'Gói'), ('SP-BK-006', 'Gói'),
    ('SP-BK-007', 'Gói'), ('SP-BK-008', 'Gói'), ('SP-BK-009', 'Gói'),
    ('SP-BK-010', 'Hộp'),
    -- Gia vị
    ('SP-GV-001', 'Chai'), ('SP-GV-002', 'Chai'), ('SP-GV-003', 'Chai'),
    ('SP-GV-004', 'Chai'), ('SP-GV-005', 'Gói'), ('SP-GV-006', 'Gói'),
    ('SP-GV-007', 'Túi'), ('SP-GV-008', 'Túi'),
    -- Sữa
    ('SP-SU-001', 'Hộp'), ('SP-SU-002', 'Hộp'), ('SP-SU-003', 'Hộp'),
    ('SP-SU-004', 'Hộp'), ('SP-SU-005', 'Hũ'), ('SP-SU-006', 'Hũ'),
    ('SP-SU-007', 'Hộp'), ('SP-SU-008', 'Hộp'),
    -- Nước ngọt + Bia
    ('SP-NN-001', 'Lon'), ('SP-NN-002', 'Lon'), ('SP-NN-003', 'Lon'),
    ('SP-NN-004', 'Lon'), ('SP-NN-005', 'Lon'),
    -- Chăm sóc cá nhân
    ('SP-CS-001', 'Chai'), ('SP-CS-002', 'Chai'), ('SP-CS-003', 'Chai'),
    ('SP-CS-004', 'Tuýp'), ('SP-CS-005', 'Lăn')
) AS u(sku_code, unit_name) ON p.sku_code = u.sku_code;
```

### 3.3 Insert ProductPriceHistory

```sql
-- ============================================================
-- GIÁ VỐN & GIÁ BÁN — 1 bản ghi / sản phẩm (effective_date hiện tại)
-- ============================================================

INSERT INTO productpricehistory (product_id, unit_id, cost_price, sale_price, effective_date)
SELECT p.id, u.id, v.cost_price, v.sale_price, CURRENT_DATE
FROM products p
JOIN productunits u ON u.product_id = p.id AND u.is_base_unit = TRUE
JOIN (VALUES
    -- Thực phẩm khô (cost, price)
    ('SP-TP-001', 3200, 4500),   ('SP-TP-002', 3200, 4500),
    ('SP-TP-003', 3000, 4200),   ('SP-TP-004', 4000, 5500),
    ('SP-TP-005', 85000, 105000), ('SP-TP-006', 72000, 90000),
    ('SP-TP-007', 12000, 17000), ('SP-TP-008', 18000, 25000),
    ('SP-TP-009', 14000, 20000), ('SP-TP-010', 18000, 25000),
    ('SP-TP-011', 10000, 15000), ('SP-TP-012', 35000, 48000),
    ('SP-TP-013', 28000, 38000), ('SP-TP-014', 25000, 35000),
    ('SP-TP-015', 8000, 12000),
    -- Đồ uống
    ('SP-DU-001', 3000, 5000),   ('SP-DU-002', 5000, 8000),
    ('SP-DU-003', 4500, 7000),   ('SP-DU-004', 5000, 8000),
    ('SP-DU-005', 5500, 9000),   ('SP-DU-006', 8000, 12000),
    ('SP-DU-007', 6000, 10000),  ('SP-DU-008', 7000, 11000),
    -- Hóa phẩm
    ('SP-HP-001', 18000, 26000), ('SP-HP-002', 14000, 20000),
    ('SP-HP-003', 55000, 75000), ('SP-HP-004', 48000, 65000),
    ('SP-HP-005', 30000, 42000), ('SP-HP-006', 25000, 35000),
    ('SP-HP-007', 8000, 12000),  ('SP-HP-008', 15000, 22000),
    -- Đồ gia dụng
    ('SP-DD-001', 6000, 10000),  ('SP-DD-002', 12000, 18000),
    ('SP-DD-003', 8000, 13000),  ('SP-DD-004', 12000, 18000),
    ('SP-DD-005', 20000, 30000),
    -- Bánh kẹo
    ('SP-BK-001', 18000, 25000), ('SP-BK-002', 18000, 25000),
    ('SP-BK-003', 9000, 14000),  ('SP-BK-004', 8000, 12000),
    ('SP-BK-005', 15000, 22000), ('SP-BK-006', 12000, 18000),
    ('SP-BK-007', 10000, 15000), ('SP-BK-008', 8000, 12000),
    ('SP-BK-009', 10000, 15000), ('SP-BK-010', 28000, 38000),
    -- Gia vị
    ('SP-GV-001', 20000, 32000), ('SP-GV-002', 25000, 38000),
    ('SP-GV-003', 28000, 38000), ('SP-GV-004', 25000, 35000),
    ('SP-GV-005', 30000, 42000), ('SP-GV-006', 8000, 12000),
    ('SP-GV-007', 15000, 22000), ('SP-GV-008', 3000, 5000),
    -- Sữa
    ('SP-SU-001', 22000, 30000), ('SP-SU-002', 24000, 32000),
    ('SP-SU-003', 18000, 25000), ('SP-SU-004', 5000, 8000),
    ('SP-SU-005', 3000, 5000),   ('SP-SU-006', 3500, 6000),
    ('SP-SU-007', 16000, 22000), ('SP-SU-008', 6000, 10000),
    -- Bia & Nước ngọt
    ('SP-NN-001', 5000, 8000),   ('SP-NN-002', 5000, 8000),
    ('SP-NN-003', 8000, 12000),  ('SP-NN-004', 10000, 15000),
    ('SP-NN-005', 6000, 10000),
    -- Chăm sóc cá nhân
    ('SP-CS-001', 28000, 40000), ('SP-CS-002', 28000, 40000),
    ('SP-CS-003', 25000, 36000), ('SP-CS-004', 12000, 18000),
    ('SP-CS-005', 22000, 32000)
) AS v(sku_code, cost_price, sale_price) ON p.sku_code = v.sku_code;
```

---

## 4. Lưu ý khi chạy

| Mục | Ghi chú |
|-----|---------|
| **Thứ tự** | Chạy 3.1 → 3.2 → 3.3 (không phụ thuộc lẫn nhau ngoài FK) |
| **Idempotent** | SKU đã tồn tại → lỗi UNIQUE. Dùng `ON CONFLICT (sku_code) DO NOTHING` nếu muốn an toàn |
| **Category ID** | Script dùng `SELECT ... WHERE category_code = '...'` để không phụ thuộc ID cứng |
| **Ảnh hưởng inventory** | Chạy xong thì **Inventory vẫn rỗng** cho các SP mới. Cần seed inventory riêng nếu muốn SP có tồn. |
| **Xoá SP cũ** | Sau khi chạy có thể xoá 50 SP "Hàng seed demo #N" (V8) bằng `DELETE FROM products WHERE sku_code LIKE 'BULK-SEED-%'` |
