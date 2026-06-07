-- Seed dữ liệu tiệm tạp hóa, thay thế dữ liệu cũ từ V6/V8/V16.
-- Nguồn: docs/dev/frontend/database/SEED_DATA_MOCK.md
-- Giả định V1 đã tạo Categories(CAT001-CAT004), WarehouseLocations(1-5), Users, Roles.

-- ============================================================
-- 1) XOÁ DỮ LIỆU CŨ (từ V6, V8, V16)
-- ============================================================
-- Xoá các bảng con trước (tôn trọng FK)
DELETE FROM InventoryLogs WHERE product_id IN (SELECT id FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%');
DELETE FROM StockReceiptDetails WHERE product_id IN (SELECT id FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%');
DELETE FROM OrderDetails WHERE product_id IN (SELECT id FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%');
DELETE FROM Inventory WHERE product_id IN (SELECT id FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%');
DELETE FROM ProductPriceHistory WHERE product_id IN (SELECT id FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%');
DELETE FROM ProductUnits WHERE product_id IN (SELECT id FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%');
DELETE FROM Products WHERE sku_code LIKE 'DEMO-%' OR sku_code LIKE 'BULK-SEED-%';
DELETE FROM Categories WHERE category_code LIKE 'DM50_%' OR category_code IN ('CAT005', 'CAT006');

-- ============================================================
-- 2) CẬP NHẬT DANH MỤC GỐC (CAT001-CAT004 từ V1)
-- ============================================================
UPDATE Categories SET name='Gia vị & Thực phẩm khô', description='Mì gói, nước mắm, dầu ăn, gia vị, gạo, đường, muối' WHERE category_code='CAT001';
UPDATE Categories SET name='Nước giải khát',       description='Nước ngọt, bia, nước suối, trà, cà phê, sữa, nước trái cây' WHERE category_code='CAT002';
UPDATE Categories SET name='Hóa phẩm & Tẩy rửa',    description='Bột giặt, nước xả, nước rửa chén, nước lau sàn' WHERE category_code='CAT003';
UPDATE Categories SET name='Vật dụng gia đình',      description='Ly chén, dao kéo, đồ nhựa gia dụng' WHERE category_code='CAT004';

-- ============================================================
-- 3) THÊM DANH MỤC CẤP 1 MỚI
-- ============================================================
INSERT INTO Categories (category_code, name, description, sort_order) VALUES
('CAT005', 'Bánh kẹo & Snack',  'Bánh quy, kẹo, snack, socola, bánh ngọt, bánh ăn dặm', 5),
('CAT006', 'Chăm sóc cá nhân',  'Xà phòng, dầu gội, sữa tắm, kem đánh răng, khăn giấy, tã', 6)
ON CONFLICT (category_code) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description;

-- ============================================================
-- 4) THÊM DANH MỤC CẤP 2 (22 danh mục con)
-- ============================================================
INSERT INTO Categories (category_code, name, parent_id, sort_order)
SELECT v.code, v.name, c.id, v.sort
FROM (VALUES
    ('CAT00101', 'Mì gói & miến',           'CAT001', 1),
    ('CAT00102', 'Nước mắm & nước tương',   'CAT001', 2),
    ('CAT00103', 'Hạt nêm & bột ngọt',      'CAT001', 3),
    ('CAT00104', 'Dầu ăn',                  'CAT001', 4),
    ('CAT00105', 'Gạo, đường, muối',         'CAT001', 5),
    ('CAT00201', 'Nước ngọt có gas',         'CAT002', 1),
    ('CAT00202', 'Bia',                      'CAT002', 2),
    ('CAT00203', 'Nước suối & tinh khiết',   'CAT002', 3),
    ('CAT00204', 'Trà & cà phê',             'CAT002', 4),
    ('CAT00205', 'Sữa tươi & sữa chua',      'CAT002', 5),
    ('CAT00206', 'Nước trái cây',            'CAT002', 6),
    ('CAT00301', 'Bột giặt & nước giặt',     'CAT003', 1),
    ('CAT00302', 'Nước xả vải',              'CAT003', 2),
    ('CAT00303', 'Nước rửa chén',            'CAT003', 3),
    ('CAT00304', 'Nước lau sàn & vệ sinh',   'CAT003', 4),
    ('CAT00401', 'Ly chén dĩa & hộp đựng',   'CAT004', 1),
    ('CAT00402', 'Dao kéo dụng cụ bếp',      'CAT004', 2),
    ('CAT00403', 'Đồ nhựa gia dụng',         'CAT004', 3),
    ('CAT00501', 'Bánh quy & bánh bông lan', 'CAT005', 1),
    ('CAT00502', 'Kẹo các loại',             'CAT005', 2),
    ('CAT00503', 'Socola & bánh ngọt',       'CAT005', 3),
    ('CAT00504', 'Snack',                    'CAT005', 4),
    ('CAT00601', 'Xà phòng & dầu gội',       'CAT006', 1),
    ('CAT00602', 'Sữa tắm',                  'CAT006', 2),
    ('CAT00603', 'Kem đánh răng & bàn chải', 'CAT006', 3),
    ('CAT00604', 'Khăn giấy, tã & vệ sinh',  'CAT006', 4)
) AS v(code, name, parent_code, sort)
JOIN Categories c ON c.category_code = v.parent_code;

-- ============================================================
-- 5) NHÀ CUNG CẤP (21)
-- ============================================================
INSERT INTO Suppliers (supplier_code, name, contact_person, phone, address) VALUES
('NCC001', 'Mondelez Kinh Đô VN',     'Phòng KD', '1900xxxx', 'KCN Biên Hòa, Đồng Nai'),
('NCC002', 'Bánh kẹo Hải Hà',        'Phòng KD', '1900xxxx', '25-27 Trương Định, Hai Bà Trưng, HN'),
('NCC003', 'Orion Vina',              'Phòng KD', '1900xxxx', 'KCN Sóng Thần, Bình Dương'),
('NCC004', 'Bibica',                  'Phòng KD', '1900xxxx', 'Long An'),
('NCC005', 'Nestlé VN',               'Phòng KD', '1900xxxx', 'KCN Đồng Nai'),
('NCC006', 'Bánh kẹo Tràng An',       'Phòng KD', '1900xxxx', 'Hà Nội'),
('NCC007', 'Bánh kẹo Biển Xanh',      'Phòng KD', '1900xxxx', 'Hà Nội'),
('NCC008', 'Suntory PepsiCo VN',      'Phòng KD', '1900xxxx', 'KCN Bình Dương'),
('NCC009', 'Coca-Cola VN',            'Phòng KD', '1900xxxx', 'Hà Nội, Đà Nẵng, TP.HCM'),
('NCC010', 'Vinamilk',                'Phòng KD', '1900xxxx', 'TP.HCM'),
('NCC011', 'Masan Consumer',          'Phòng KD', '1900xxxx', 'TP.HCM'),
('NCC012', 'Sabeco (Bia SG)',         'Phòng KD', '1900xxxx', 'TP.HCM'),
('NCC013', 'Unilever VN',             'Phòng KD', '1900xxxx', 'Củ Chi, TP.HCM'),
('NCC014', 'P&G VN',                  'Phòng KD', '1900xxxx', 'KCN Bình Dương'),
('NCC015', 'Nhựa Duy Tân',            'Phòng KD', '1900xxxx', 'Bình Tân, TP.HCM'),
('NCC016', 'Kềm Nghĩa',               'Phòng KD', '1900xxxx', 'Bình Dương'),
('NCC017', 'Acecook VN',              'Phòng KD', '1900xxxx', 'Bình Chánh, TP.HCM'),
('NCC018', 'Dầu Tường An',            'Phòng KD', '1900xxxx', 'Biên Hòa, Đồng Nai'),
('NCC019', 'Bách Hóa Xanh (BHX)',     'Phòng KD', '1900xxxx', 'TP.HCM'),
('NCC020', 'Giấy Tân Tiến',           'Phòng KD', '1900xxxx', 'TP.HCM'),
('NCC021', 'Kido',                    'Phòng KD', '1900xxxx', 'TP.HCM')
ON CONFLICT (supplier_code) DO NOTHING;

-- ============================================================
-- 6) SẢN PHẨM (149)
-- ============================================================
WITH sp AS (
    SELECT * FROM (VALUES
    -- 6.1 Bánh kẹo & Snack > Bánh quy & bánh bông lan
    ('SP001','Bánh Oreo vị kem vani 134g',       'CAT00501','NCC001',10000,15000,'Gói'),
    ('SP002','Bánh Oreo vị kem socola 134g',     'CAT00501','NCC001',10000,15000,'Gói'),
    ('SP003','Bánh Cosy vị kem sữa 144g',         'CAT00501','NCC001', 7500,11000,'Gói'),
    ('SP004','Bánh Cosy vị socola 144g',          'CAT00501','NCC001', 7500,11000,'Gói'),
    ('SP005','Bánh Solite bông lan cuộn kem dâu 360g','CAT00501','NCC001',25000,35000,'Hộp'),
    ('SP006','Bánh Solite bông lan cuộn kem lá dứa 360g','CAT00501','NCC001',25000,35000,'Hộp'),
    ('SP007','Bánh AFC vị bơ tỏi 200g',           'CAT00501','NCC001', 8000,12000,'Gói'),
    ('SP008','Bánh Ritz hương phô mai 147g',      'CAT00501','NCC001',14000,20000,'Gói'),
    ('SP009','Bánh gạo One One vị rong biển 100g','CAT00501','NCC001', 5000, 7500,'Gói'),
    ('SP010','Bánh LU Pháp bơ thập cẩm 400g',    'CAT00501','NCC001',85000,115000,'Hộp'),
    ('SP011','Bánh quy Hải Hà bơ sữa 200g',      'CAT00501','NCC002', 8500,12000,'Gói'),
    ('SP012','Bánh quy Hải Hà socola 200g',      'CAT00501','NCC002', 9000,13000,'Gói'),
    ('SP013','Bánh kem xốp Hải Hà vị dâu 150g',  'CAT00501','NCC002', 6500, 9500,'Gói'),
    ('SP014','Bánh kem xốp Hải Hà vị socola 150g','CAT00501','NCC002', 6500, 9500,'Gói'),
    ('SP015','Bánh quy Hải Hà lúa mạch 200g',    'CAT00501','NCC002', 8000,12000,'Gói'),
    ('SP016','Bánh bông lan cuộn kem Hura bơ sữa 360g','CAT00501','NCC004',22000,32000,'Hộp'),
    ('SP017','Bánh bông lan cuộn kem Hura cam 360g','CAT00501','NCC004',22000,32000,'Hộp'),
    ('SP018','Bánh bông lan cuộn kem Hura cốm 360g','CAT00501','NCC004',22000,32000,'Hộp'),
    -- 6.2 Bánh kẹo & Snack > Kẹo các loại
    ('SP019','Kẹo cứng Hải Hà vị trái cây 300g', 'CAT00502','NCC002',12000,18000,'Túi'),
    ('SP020','Kẹo mềm Hải Hà vị sữa 200g',       'CAT00502','NCC002',10000,15000,'Túi'),
    ('SP021','Kẹo dẻo Hải Hà vị trái cây 200g',  'CAT00502','NCC002',11000,16000,'Túi'),
    ('SP022','Kẹo Chew Hải Hà vị dâu 140g',      'CAT00502','NCC002', 9000,14000,'Túi'),
    ('SP023','Kẹo dẻo Kido vị trái cây 100g',    'CAT00502','NCC021', 6000, 9000,'Túi'),
    ('SP024','Kẹo dẻo Kido vị sữa 100g',         'CAT00502','NCC021', 6000, 9000,'Túi'),
    -- 6.3 Bánh kẹo & Snack > Socola & bánh ngọt
    ('SP025','Socola KitKat 4 thanh 42g',         'CAT00503','NCC005', 7500,11000,'Gói'),
    ('SP026','Kẹo cao su Doublemint 12 viên',    'CAT00503','NCC005', 4000, 6000,'Vỉ'),
    ('SP027','ChocoPie Orion 336g (12 cái)',     'CAT00503','NCC003',28000,39000,'Hộp'),
    ('SP028','Custas Orion vị trứng 288g',       'CAT00503','NCC003',25000,35000,'Hộp'),
    ('SP029','Custas Orion vị socola 288g',      'CAT00503','NCC003',25000,35000,'Hộp'),
    ('SP030','Bánh xốp Orion dâu kem 216g',      'CAT00503','NCC003',22000,32000,'Hộp'),
    ('SP031','Bánh ăn dặm Cerelac Nestlé gạo 200g','CAT00503','NCC005',25000,35000,'Hộp'),
    ('SP032','Bánh ăn dặm Growsure Bibica 168g', 'CAT00503','NCC004',18000,25000,'Hộp'),
    -- 6.4 Bánh kẹo & Snack > Snack
    ('SP033','Snack Poca vị tôm cay 85g',         'CAT00504','NCC008', 5500, 8000,'Gói'),
    ('SP034','Snack Poca vị phô mai 85g',         'CAT00504','NCC008', 5500, 8000,'Gói'),
    ('SP035','Snack Lay''s vị tự nhiên 52g',      'CAT00504','NCC008', 4500, 7000,'Gói'),
    ('SP036','Snack Lay''s vị thịt nướng 52g',    'CAT00504','NCC008', 4500, 7000,'Gói'),
    ('SP037','Snack Oishi vị tàu hủ ky 100g',     'CAT00504','NCC008', 5000, 8000,'Gói'),
    ('SP038','Bánh gòn Oishi đường đen 120g',     'CAT00504','NCC008', 6000, 9000,'Gói'),
    ('SP039','Snack khoai tây Slide tự nhiên 90g','CAT00504','NCC001',10000,15000,'Hộp'),
    -- 6.5 Nước giải khát > Nước ngọt có gas
    ('SP040','Pepsi cola lon 330ml',               'CAT00201','NCC008', 5000, 8000,'Lon'),
    ('SP041','Pepsi cola chai 600ml',              'CAT00201','NCC008', 6500,10000,'Chai'),
    ('SP042','Pepsi không calo lon 330ml',         'CAT00201','NCC008', 5000, 8000,'Lon'),
    ('SP043','7Up lon 330ml',                      'CAT00201','NCC008', 5000, 8000,'Lon'),
    ('SP044','Mirinda vị cam lon 330ml',           'CAT00201','NCC008', 5000, 8000,'Lon'),
    ('SP045','Mirinda vị nho lon 330ml',           'CAT00201','NCC008', 5000, 8000,'Lon'),
    ('SP046','Sting vàng lon 330ml',               'CAT00201','NCC008', 6000, 9000,'Lon'),
    ('SP047','Coca-Cola lon 330ml',                'CAT00201','NCC009', 5000, 8000,'Lon'),
    ('SP048','Coca-Cola chai 600ml',               'CAT00201','NCC009', 6500,10000,'Chai'),
    ('SP049','Sprite lon 330ml',                   'CAT00201','NCC009', 5000, 8000,'Lon'),
    ('SP050','Fanta cam lon 330ml',                'CAT00201','NCC009', 5000, 8000,'Lon'),
    -- 6.6 Nước giải khát > Bia
    ('SP051','Bia Sài Gòn lager lon 330ml',        'CAT00202','NCC012', 6500,10000,'Lon'),
    ('SP052','Bia 333 lon 330ml',                  'CAT00202','NCC012', 6000, 9500,'Lon'),
    ('SP053','Bia Sài Gòn Special lon 330ml',      'CAT00202','NCC012', 7000,11000,'Lon'),
    ('SP054','Bia Sài Gòn chai 355ml',             'CAT00202','NCC012', 7500,11500,'Chai'),
    -- 6.7 Nước giải khát > Nước suối & tinh khiết
    ('SP055','Aquafina chai 1.5L',                 'CAT00203','NCC008', 5000, 8000,'Chai'),
    ('SP056','Aquafina chai 500ml',                'CAT00203','NCC008', 3000, 5000,'Chai'),
    ('SP057','La Vie chai 1.5L',                   'CAT00203','NCC005', 4000, 6500,'Chai'),
    ('SP058','La Vie chai 500ml',                  'CAT00203','NCC005', 2500, 4000,'Chai'),
    ('SP059','Dasani chai 1.5L',                   'CAT00203','NCC009', 4000, 6500,'Chai'),
    -- 6.8 Nước giải khát > Trà & cà phê
    ('SP060','Trà xanh C2 chai 1.5L',              'CAT00204','NCC011', 8000,12000,'Chai'),
    ('SP061','Trà xanh C2 chai 500ml',             'CAT00204','NCC011', 4500, 7000,'Chai'),
    ('SP062','Trà sữa xanh C2 hũ 300ml',           'CAT00204','NCC011', 6000, 9000,'Hũ'),
    ('SP063','Cà phê Nescafe hòa tan 100g',        'CAT00204','NCC005',30000,42000,'Hộp'),
    ('SP064','Nescafe sữa hòa tan 120g',           'CAT00204','NCC005',28000,40000,'Hộp'),
    -- 6.9 Nước giải khát > Sữa tươi & sữa chua
    ('SP065','Sữa tươi Vinamilk không đường 1L',   'CAT00205','NCC010',20000,28000,'Hộp'),
    ('SP066','Sữa tươi Vinamilk có đường 1L',      'CAT00205','NCC010',20000,28000,'Hộp'),
    ('SP067','Sữa tươi Vinamilk ít đường 1L',      'CAT00205','NCC010',20000,28000,'Hộp'),
    ('SP068','Sữa chua Vinamilk đường trắng 100g x4','CAT00205','NCC010',10000,15000,'Lốc'),
    ('SP069','Sữa chua Vinamilk không đường 100g x4','CAT00205','NCC010',10000,15000,'Lốc'),
    ('SP070','Sữa chua uống Vinamilk 180ml x4',    'CAT00205','NCC010',12000,18000,'Lốc'),
    ('SP071','Nước cam ép Vinamilk 1L',            'CAT00206','NCC010',18000,25000,'Hộp'),
    ('SP072','Milo hộp 180ml',                     'CAT00205','NCC005', 5500, 8000,'Hộp'),
    ('SP073','Milo hộp 115ml',                     'CAT00205','NCC005', 3500, 5500,'Hộp'),
    -- 6.10 Hóa phẩm > Bột giặt & nước giặt
    ('SP074','Bột giặt Omo công thức xanh 1.8kg',  'CAT00301','NCC013',55000,75000,'Túi'),
    ('SP075','Bột giặt Omo công thức xanh 800g',   'CAT00301','NCC013',28000,40000,'Túi'),
    ('SP076','Nước giặt OMO Matic oải hương 3.8kg','CAT00301','NCC013',100000,138000,'Túi'),
    ('SP077','Bột giặt Tide 1.2kg',                'CAT00301','NCC014',45000,62000,'Túi'),
    ('SP078','Nước giặt Tide thơm 1.36L',          'CAT00301','NCC014',50000,68000,'Chai'),
    ('SP079','Bột giặt Surf hương nước xả 2kg',    'CAT00301','NCC013',38000,52000,'Túi'),
    ('SP080','Bột giặt Surf 800g',                 'CAT00301','NCC013',18000,26000,'Túi'),
    -- 6.11 Hóa phẩm > Nước xả vải
    ('SP081','Nước xả Comfort hương nước hoa 2L',  'CAT00302','NCC013',45000,62000,'Chai'),
    ('SP082','Nước xả Comfort hương thiên nhiên 2L','CAT00302','NCC013',45000,62000,'Chai'),
    ('SP083','Nước xả Downy hương nước hoa Pháp 2L','CAT00302','NCC014',50000,68000,'Chai'),
    ('SP084','Nước xả Downy hương oải hương 2L',   'CAT00302','NCC014',50000,68000,'Chai'),
    -- 6.12 Hóa phẩm > Nước rửa chén
    ('SP085','Nước rửa chén Sunlight chanh 750ml', 'CAT00303','NCC013',20000,30000,'Chai'),
    ('SP086','Nước rửa chén Sunlight thiên nhiên 750ml','CAT00303','NCC013',22000,32000,'Chai'),
    ('SP087','Nước rửa chén Joy tinh chất chanh 700ml','CAT00303','NCC014',22000,32000,'Chai'),
    -- 6.13 Hóa phẩm > Nước lau sàn & vệ sinh
    ('SP088','Nước lau sàn Vim hương thiên nhiên 2L','CAT00304','NCC013',30000,42000,'Chai'),
    ('SP089','Nước lau sàn Vim hoa oải hương 2L',  'CAT00304','NCC013',30000,42000,'Chai'),
    ('SP090','Nước lau kính Vim 500ml',            'CAT00304','NCC013',18000,26000,'Chai'),
    ('SP091','Xịt tẩy vệ sinh Vim nhà tắm 500ml',  'CAT00304','NCC013',22000,32000,'Chai'),
    ('SP092','Nước tẩy bếp Cif 500ml',              'CAT00304','NCC013',25000,35000,'Chai'),
    -- 6.14 Vật dụng gia đình > Ly chén dĩa & hộp đựng
    ('SP093','Ly nhựa Duy Tân trong suốt 250ml x50','CAT00401','NCC015',30000,42000,'Bịch'),
    ('SP094','Ly giấy Duy Tân 200ml x50',          'CAT00401','NCC015',25000,35000,'Bịch'),
    ('SP095','Hộp nhựa Duy Tân tròn 1.5L có nắp',  'CAT00401','NCC015',22000,32000,'Cái'),
    ('SP096','Rổ nhựa Duy Tân đa năng cỡ vừa',     'CAT00403','NCC015',15000,22000,'Cái'),
    ('SP097','Thùng nhựa Duy Tân 60L có nắp',      'CAT00403','NCC015',80000,110000,'Cái'),
    -- 6.15 Vật dụng gia đình > Dao kéo dụng cụ bếp
    ('SP098','Kéo inox Kềm Nghĩa 20cm cán nhựa',   'CAT00402','NCC016',25000,35000,'Cái'),
    ('SP099','Dao inox Kềm Nghĩa lưỡi lớn 20cm',   'CAT00402','NCC016',35000,50000,'Cái'),
    ('SP100','Kềm bấm móng Kềm Nghĩa inox',         'CAT00402','NCC016',18000,28000,'Cái'),
    ('SP101','Bộ thìa dĩa inox Kềm Nghĩa 12 món',  'CAT00402','NCC016',28000,40000,'Bộ'),
    -- 6.16 Gia vị & TP khô > Mì gói & miến
    ('SP102','Mì Hảo Hảo tôm chua cay 75g',         'CAT00101','NCC017', 2500, 3500,'Gói'),
    ('SP103','Mì Hảo Hảo sườn heo 75g',            'CAT00101','NCC017', 2500, 3500,'Gói'),
    ('SP104','Mì Đệ Nhất tôm 75g',                 'CAT00101','NCC017', 2000, 3000,'Gói'),
    ('SP105','Mì Omachi tôm hùm 90g',              'CAT00101','NCC017', 4000, 6000,'Gói'),
    ('SP106','Miến Goodle 60g',                    'CAT00101','NCC017', 3000, 4500,'Gói'),
    -- 6.17 Gia vị & TP khô > Nước mắm & nước tương
    ('SP107','Nước mắm Nam Ngư 500ml',             'CAT00102','NCC011',15000,22000,'Chai'),
    ('SP108','Nước mắm Nam Ngư 1L',                'CAT00102','NCC011',25000,35000,'Chai'),
    ('SP109','Nước tương Tam Thái Tử 500ml',       'CAT00102','NCC011',12000,18000,'Chai'),
    ('SP110','Sốt cà chua Masan 340g',              'CAT00102','NCC011', 8000,12500,'Gói'),
    ('SP111','Tương ớt Cholimex 250g',             'CAT00102','NCC011', 7000,11000,'Chai'),
    -- 6.18 Gia vị & TP khô > Hạt nêm & bột ngọt
    ('SP112','Hạt nêm Knorr từ thịt thăn 400g',    'CAT00103','NCC011',18000,25000,'Túi'),
    ('SP113','Hạt nêm Knorr gà 400g',              'CAT00103','NCC011',18000,25000,'Túi'),
    ('SP114','Bột ngọt Ajinomoto 200g',            'CAT00103','NCC011',12000,17000,'Túi'),
    ('SP115','Bột ngọt Ajinomoto 500g',            'CAT00103','NCC011',25000,35000,'Túi'),
    ('SP116','Bột canh Hải Châu 200g',             'CAT00103','NCC011', 6000,10000,'Gói'),
    ('SP117','Bột canh Hải Châu iot 200g',         'CAT00103','NCC011', 6500,10500,'Gói'),
    -- 6.19 Gia vị & TP khô > Dầu ăn
    ('SP118','Dầu ăn Tường An 1L',                 'CAT00104','NCC018',25000,35000,'Chai'),
    ('SP119','Dầu ăn Tường An 5L',                 'CAT00104','NCC018',100000,140000,'Can'),
    ('SP120','Dầu ăn Neptuna 1L',                  'CAT00104','NCC018',28000,40000,'Chai'),
    ('SP121','Dầu ăn Simply 1L',                   'CAT00104','NCC018',22000,32000,'Chai'),
    -- 6.20 Gia vị & TP khô > Gạo, đường, muối
    ('SP122','Gạo thơm 5kg',                        'CAT00105','NCC019',55000,75000,'Túi'),
    ('SP123','Gạo Nàng Nhen 5kg',                   'CAT00105','NCC019',65000,90000,'Túi'),
    ('SP124','Đường cát trắng tinh luyện 1kg',      'CAT00105','NCC019',12000,17000,'Túi'),
    ('SP125','Muối iot 500g',                      'CAT00105','NCC019', 3000, 5000,'Túi'),
    -- 6.21 Chăm sóc cá nhân > Xà phòng & dầu gội
    ('SP126','Xà phòng Lifebuoy diệt khuẩn 90g',    'CAT00601','NCC013', 6500,10000,'Bánh'),
    ('SP127','Xà phòng Lifebuoy bộ 3 bánh 90g x3', 'CAT00601','NCC013',17000,25000,'Hộp'),
    ('SP128','Dầu gội Clear ngăn rụng tóc 360ml',   'CAT00601','NCC013',45000,62000,'Chai'),
    ('SP129','Dầu gội Clear mát lạnh 360ml',        'CAT00601','NCC013',45000,62000,'Chai'),
    ('SP130','Dầu gội Sunsilk mềm mượt 360ml',     'CAT00601','NCC013',40000,56000,'Chai'),
    ('SP131','Dầu gội Pantene suôn mượt 360ml',    'CAT00601','NCC014',48000,66000,'Chai'),
    ('SP132','Dầu gội Head & Shoulders gàu 360ml', 'CAT00601','NCC014',50000,68000,'Chai'),
    ('SP133','Dầu gội Rejoice mượt tóc 360ml',     'CAT00601','NCC014',42000,58000,'Chai'),
    -- 6.22 Chăm sóc cá nhân > Sữa tắm
    ('SP134','Sữa tắm Lifebuoy diệt khuẩn 450ml',  'CAT00602','NCC013',38000,55000,'Chai'),
    ('SP135','Sữa tắm Dove dưỡng ẩm 500ml',        'CAT00602','NCC013',50000,70000,'Chai'),
    ('SP136','Sữa tắm Lux quyến rũ 450ml',          'CAT00602','NCC013',35000,50000,'Chai'),
    ('SP137','Lăn khử mùi Rexona xịt 50ml',        'CAT00602','NCC013',28000,40000,'Chai'),
    -- 6.23 Chăm sóc cá nhân > Kem đánh răng & bàn chải
    ('SP138','Kem đánh răng Crest trắng răng 120g','CAT00603','NCC014',18000,28000,'Tuýp'),
    ('SP139','Kem đánh răng P/S chống sâu răng 120g','CAT00603','NCC013',12000,18000,'Tuýp'),
    ('SP140','Kem đánh răng P/S trắng răng 120g',   'CAT00603','NCC013',13000,20000,'Tuýp'),
    ('SP141','Bàn chải đánh răng Oral-B mềm',       'CAT00603','NCC014',15000,22000,'Cái'),
    ('SP142','Bàn chải đánh răng P/S',             'CAT00603','NCC013', 8000,12000,'Cái'),
    -- 6.24 Chăm sóc cá nhân > Khăn giấy, tã & vệ sinh
    ('SP143','Khăn giấy ướt Bobby 80 tờ',          'CAT00604','NCC020',10000,15000,'Hộp'),
    ('SP144','Giấy vệ sinh Bobby cuộn 4 cuộn',     'CAT00604','NCC020',18000,28000,'Bịch'),
    ('SP145','Khăn giấy mặt Bobby cao cấp 100 tờ', 'CAT00604','NCC020', 8000,12000,'Hộp'),
    ('SP146','Khăn giấy ăn Bobby 200 tờ',          'CAT00604','NCC020', 5000, 8000,'Bịch'),
    ('SP147','Tã quần Bobby size M (6-11kg) 42 cái','CAT00604','NCC020',85000,120000,'Bịch'),
    ('SP148','Tã quần Bobby size L (9-14kg) 36 cái','CAT00604','NCC020',88000,125000,'Bịch'),
    ('SP149','Băng vệ sinh Kotex trung bình 10 miếng','CAT00604','NCC014',18000,25000,'Gói')
    ) AS t
)
INSERT INTO Products (category_id, sku_code, name, status)
SELECT c.id, t.sku, t.name, 'Active'
FROM sp t
JOIN Categories c ON c.category_code = t.cat_code
ON CONFLICT (sku_code) DO NOTHING;

-- ============================================================
-- 7) ĐƠN VỊ CƠ SỞ (149 products x 1 base unit)
-- ============================================================
WITH sp AS (
    SELECT * FROM (VALUES
    ('SP001','Gói'),('SP002','Gói'),('SP003','Gói'),('SP004','Gói'),
    ('SP005','Hộp'),('SP006','Hộp'),('SP007','Gói'),('SP008','Gói'),
    ('SP009','Gói'),('SP010','Hộp'),('SP011','Gói'),('SP012','Gói'),
    ('SP013','Gói'),('SP014','Gói'),('SP015','Gói'),('SP016','Hộp'),
    ('SP017','Hộp'),('SP018','Hộp'),('SP019','Túi'),('SP020','Túi'),
    ('SP021','Túi'),('SP022','Túi'),('SP023','Túi'),('SP024','Túi'),
    ('SP025','Gói'),('SP026','Vỉ'), ('SP027','Hộp'),('SP028','Hộp'),
    ('SP029','Hộp'),('SP030','Hộp'),('SP031','Hộp'),('SP032','Hộp'),
    ('SP033','Gói'),('SP034','Gói'),('SP035','Gói'),('SP036','Gói'),
    ('SP037','Gói'),('SP038','Gói'),('SP039','Hộp'),
    ('SP040','Lon'),('SP041','Chai'),('SP042','Lon'),('SP043','Lon'),
    ('SP044','Lon'),('SP045','Lon'),('SP046','Lon'),
    ('SP047','Lon'),('SP048','Chai'),('SP049','Lon'),('SP050','Lon'),
    ('SP051','Lon'),('SP052','Lon'),('SP053','Lon'),('SP054','Chai'),
    ('SP055','Chai'),('SP056','Chai'),('SP057','Chai'),('SP058','Chai'),
    ('SP059','Chai'),
    ('SP060','Chai'),('SP061','Chai'),('SP062','Hũ'), ('SP063','Hộp'),('SP064','Hộp'),
    ('SP065','Hộp'),('SP066','Hộp'),('SP067','Hộp'),
    ('SP068','Lốc'),('SP069','Lốc'),('SP070','Lốc'),
    ('SP071','Hộp'),('SP072','Hộp'),('SP073','Hộp'),
    ('SP074','Túi'),('SP075','Túi'),('SP076','Túi'),
    ('SP077','Túi'),('SP078','Chai'),
    ('SP079','Túi'),('SP080','Túi'),
    ('SP081','Chai'),('SP082','Chai'),('SP083','Chai'),('SP084','Chai'),
    ('SP085','Chai'),('SP086','Chai'),('SP087','Chai'),
    ('SP088','Chai'),('SP089','Chai'),('SP090','Chai'),('SP091','Chai'),('SP092','Chai'),
    ('SP093','Bịch'),('SP094','Bịch'),('SP095','Cái'),
    ('SP096','Cái'),('SP097','Cái'),
    ('SP098','Cái'),('SP099','Cái'),('SP100','Cái'),('SP101','Bộ'),
    ('SP102','Gói'),('SP103','Gói'),('SP104','Gói'),('SP105','Gói'),('SP106','Gói'),
    ('SP107','Chai'),('SP108','Chai'),('SP109','Chai'),('SP110','Gói'),('SP111','Chai'),
    ('SP112','Túi'),('SP113','Túi'),('SP114','Túi'),('SP115','Túi'),('SP116','Gói'),('SP117','Gói'),
    ('SP118','Chai'),('SP119','Can'),('SP120','Chai'),('SP121','Chai'),
    ('SP122','Túi'),('SP123','Túi'),('SP124','Túi'),('SP125','Túi'),
    ('SP126','Bánh'),('SP127','Hộp'),
    ('SP128','Chai'),('SP129','Chai'),('SP130','Chai'),
    ('SP131','Chai'),('SP132','Chai'),('SP133','Chai'),
    ('SP134','Chai'),('SP135','Chai'),('SP136','Chai'),('SP137','Chai'),
    ('SP138','Tuýp'),('SP139','Tuýp'),('SP140','Tuýp'),
    ('SP141','Cái'),('SP142','Cái'),
    ('SP143','Hộp'),('SP144','Bịch'),('SP145','Hộp'),('SP146','Bịch'),('SP147','Bịch'),('SP148','Bịch'),('SP149','Gói')
    ) AS t
)
INSERT INTO ProductUnits (product_id, unit_name, conversion_rate, is_base_unit)
SELECT p.id, t.unit, 1.0, true
FROM sp t
JOIN Products p ON p.sku_code = t.sku
ON CONFLICT (product_id, unit_name) DO NOTHING;

-- ============================================================
-- 8) LỊCH SỬ GIÁ (149 records, hiệu lực từ 01/06/2026)
-- ============================================================
WITH sp AS (
    SELECT * FROM (VALUES
    ('SP001',10000,15000),('SP002',10000,15000),('SP003',7500,11000),('SP004',7500,11000),
    ('SP005',25000,35000),('SP006',25000,35000),('SP007',8000,12000),('SP008',14000,20000),
    ('SP009',5000,7500),('SP010',85000,115000),('SP011',8500,12000),('SP012',9000,13000),
    ('SP013',6500,9500),('SP014',6500,9500),('SP015',8000,12000),
    ('SP016',22000,32000),('SP017',22000,32000),('SP018',22000,32000),
    ('SP019',12000,18000),('SP020',10000,15000),('SP021',11000,16000),('SP022',9000,14000),
    ('SP023',6000,9000),('SP024',6000,9000),
    ('SP025',7500,11000),('SP026',4000,6000),('SP027',28000,39000),
    ('SP028',25000,35000),('SP029',25000,35000),('SP030',22000,32000),
    ('SP031',25000,35000),('SP032',18000,25000),
    ('SP033',5500,8000),('SP034',5500,8000),('SP035',4500,7000),('SP036',4500,7000),
    ('SP037',5000,8000),('SP038',6000,9000),('SP039',10000,15000),
    ('SP040',5000,8000),('SP041',6500,10000),('SP042',5000,8000),
    ('SP043',5000,8000),('SP044',5000,8000),('SP045',5000,8000),('SP046',6000,9000),
    ('SP047',5000,8000),('SP048',6500,10000),('SP049',5000,8000),('SP050',5000,8000),
    ('SP051',6500,10000),('SP052',6000,9500),('SP053',7000,11000),('SP054',7500,11500),
    ('SP055',5000,8000),('SP056',3000,5000),('SP057',4000,6500),('SP058',2500,4000),
    ('SP059',4000,6500),
    ('SP060',8000,12000),('SP061',4500,7000),('SP062',6000,9000),
    ('SP063',30000,42000),('SP064',28000,40000),
    ('SP065',20000,28000),('SP066',20000,28000),('SP067',20000,28000),
    ('SP068',10000,15000),('SP069',10000,15000),('SP070',12000,18000),
    ('SP071',18000,25000),('SP072',5500,8000),('SP073',3500,5500),
    ('SP074',55000,75000),('SP075',28000,40000),('SP076',100000,138000),
    ('SP077',45000,62000),('SP078',50000,68000),('SP079',38000,52000),('SP080',18000,26000),
    ('SP081',45000,62000),('SP082',45000,62000),('SP083',50000,68000),('SP084',50000,68000),
    ('SP085',20000,30000),('SP086',22000,32000),('SP087',22000,32000),
    ('SP088',30000,42000),('SP089',30000,42000),('SP090',18000,26000),
    ('SP091',22000,32000),('SP092',25000,35000),
    ('SP093',30000,42000),('SP094',25000,35000),('SP095',22000,32000),
    ('SP096',15000,22000),('SP097',80000,110000),
    ('SP098',25000,35000),('SP099',35000,50000),('SP100',18000,28000),('SP101',28000,40000),
    ('SP102',2500,3500),('SP103',2500,3500),('SP104',2000,3000),
    ('SP105',4000,6000),('SP106',3000,4500),
    ('SP107',15000,22000),('SP108',25000,35000),('SP109',12000,18000),
    ('SP110',8000,12500),('SP111',7000,11000),
    ('SP112',18000,25000),('SP113',18000,25000),('SP114',12000,17000),
    ('SP115',25000,35000),('SP116',6000,10000),('SP117',6500,10500),
    ('SP118',25000,35000),('SP119',100000,140000),('SP120',28000,40000),('SP121',22000,32000),
    ('SP122',55000,75000),('SP123',65000,90000),('SP124',12000,17000),('SP125',3000,5000),
    ('SP126',6500,10000),('SP127',17000,25000),
    ('SP128',45000,62000),('SP129',45000,62000),('SP130',40000,56000),
    ('SP131',48000,66000),('SP132',50000,68000),('SP133',42000,58000),
    ('SP134',38000,55000),('SP135',50000,70000),('SP136',35000,50000),('SP137',28000,40000),
    ('SP138',18000,28000),('SP139',12000,18000),('SP140',13000,20000),
    ('SP141',15000,22000),('SP142',8000,12000),
    ('SP143',10000,15000),('SP144',18000,28000),('SP145',8000,12000),
    ('SP146',5000,8000),('SP147',85000,120000),('SP148',88000,125000),('SP149',18000,25000)
    ) AS t
)
INSERT INTO ProductPriceHistory (product_id, unit_id, cost_price, sale_price, effective_date)
SELECT p.id, u.id, t.cost, t.sale, DATE '2026-06-01'
FROM sp t
JOIN Products p ON p.sku_code = t.sku
JOIN ProductUnits u ON u.product_id = p.id AND u.is_base_unit = true;

-- ============================================================
-- 9) TỒN KHO (~2 batch / sản phẩm)
-- ============================================================
INSERT INTO Inventory (product_id, location_id, batch_number, expiry_date, quantity, min_quantity)
SELECT p.id, t.lid, t.bnum, t.exp, t.qty, t.mq
FROM (VALUES
    -- Bánh quy & bánh bông lan
    ('SP001',1,'B-OREO-01',NULL,30,10),('SP002',1,'B-OREO-02',NULL,25,10),
    ('SP003',1,'B-COSY-01',NULL,40,15),('SP004',1,'B-COSY-02',NULL,35,15),
    ('SP005',1,'B-SOL-01',NULL,15,5),('SP006',1,'B-SOL-02',NULL,12,5),
    ('SP007',1,'B-AFC-01',NULL,50,20),('SP008',1,'B-RITZ-01',NULL,20,8),
    ('SP009',1,'B-ONE-01',NULL,60,20),('SP010',1,'B-LU-01',NULL,8,3),
    ('SP011',1,'B-HH-01',NULL,45,15),('SP012',1,'B-HH-02',NULL,40,15),
    ('SP013',1,'B-HH-03',NULL,35,10),('SP014',1,'B-HH-04',NULL,30,10),
    ('SP015',1,'B-HH-05',NULL,40,15),
    ('SP016',2,'B-HURA-01',NULL,20,8),('SP017',2,'B-HURA-02',NULL,18,8),('SP018',2,'B-HURA-03',NULL,22,8),
    -- Kẹo
    ('SP019',1,'K-HH-01',NULL,25,10),('SP020',1,'K-HH-02',NULL,30,10),
    ('SP021',1,'K-HH-03',NULL,20,8),('SP022',1,'K-HH-04',NULL,35,15),
    ('SP023',1,'K-KIDO-01',NULL,40,15),('SP024',1,'K-KIDO-02',NULL,45,15),
    -- Socola & bánh ngọt
    ('SP025',2,'S-KIT-01',DATE '2027-03-01',40,15),
    ('SP026',2,'S-DBL-01',DATE '2027-06-01',60,20),
    ('SP027',2,'S-CP-01',DATE '2027-02-01',15,5),
    ('SP028',2,'S-CUS-01',DATE '2027-04-01',12,5),('SP029',2,'S-CUS-02',DATE '2027-04-01',10,5),
    ('SP030',2,'S-ORI-01',DATE '2027-05-01',18,8),
    ('SP031',2,'S-CER-01',DATE '2027-08-01',10,5),('SP032',2,'S-GRW-01',DATE '2027-07-01',15,5),
    -- Snack
    ('SP033',1,'SN-POCA-01',NULL,50,20),('SP034',1,'SN-POCA-02',NULL,45,20),
    ('SP035',1,'SN-LAY-01',NULL,60,25),('SP036',1,'SN-LAY-02',NULL,55,25),
    ('SP037',1,'SN-OISHI-01',NULL,40,15),('SP038',1,'SN-OISHI-02',NULL,35,15),
    ('SP039',1,'SN-SLIDE-01',NULL,20,8),
    -- Nước ngọt có gas
    ('SP040',1,'NG-PEPSI-01',DATE '2027-09-01',72,24),
    ('SP041',1,'NG-PEPSI-02',DATE '2027-08-01',48,12),
    ('SP042',1,'NG-PEPSI-03',DATE '2027-09-01',36,12),
    ('SP043',1,'NG-7UP-01',DATE '2027-09-01',48,12),
    ('SP044',1,'NG-MIR-01',DATE '2027-09-01',36,12),('SP045',1,'NG-MIR-02',DATE '2027-09-01',36,12),
    ('SP046',1,'NG-STING-01',DATE '2027-10-01',48,12),
    ('SP047',1,'NG-COKE-01',DATE '2027-09-01',72,24),('SP048',1,'NG-COKE-02',DATE '2027-08-01',48,12),
    ('SP049',1,'NG-SPRITE-01',DATE '2027-09-01',48,12),('SP050',1,'NG-FANTA-01',DATE '2027-09-01',36,12),
    -- Bia
    ('SP051',4,'BIA-SG-01',DATE '2027-07-01',48,12),('SP052',4,'BIA-333-01',DATE '2027-07-01',36,12),
    ('SP053',4,'BIA-SGS-01',DATE '2027-08-01',24,6),('SP054',4,'BIA-SGC-01',DATE '2027-08-01',24,6),
    -- Nước suối
    ('SP055',1,'NS-AQUA-01',DATE '2028-01-01',36,12),('SP056',1,'NS-AQUA-02',DATE '2028-01-01',48,24),
    ('SP057',1,'NS-LAVIE-01',DATE '2028-02-01',36,12),('SP058',1,'NS-LAVIE-02',DATE '2028-02-01',48,24),
    ('SP059',1,'NS-DASA-01',DATE '2028-01-01',24,12),
    -- Trà & cà phê
    ('SP060',1,'TRA-C2-01',DATE '2027-11-01',24,12),('SP061',1,'TRA-C2-02',DATE '2027-11-01',36,12),
    ('SP062',1,'TRA-C2-03',DATE '2027-10-01',24,12),
    ('SP063',2,'CF-NES-01',DATE '2028-03-01',10,5),('SP064',2,'CF-NES-02',DATE '2028-03-01',8,5),
    -- Sữa & nước trái cây
    ('SP065',2,'SUA-VM-01',DATE '2026-09-01',24,12),('SP066',2,'SUA-VM-02',DATE '2026-09-01',24,12),
    ('SP067',2,'SUA-VM-03',DATE '2026-09-01',24,12),
    ('SP068',2,'SC-VM-01',DATE '2026-08-01',30,12),('SP069',2,'SC-VM-02',DATE '2026-08-01',30,12),
    ('SP070',2,'SCU-VM-01',DATE '2026-08-01',24,12),
    ('SP071',2,'NC-VM-01',DATE '2026-10-01',18,6),
    ('SP072',2,'MILO-01',DATE '2026-12-01',36,12),('SP073',2,'MILO-02',DATE '2026-12-01',48,12),
    -- Bột giặt & nước giặt
    ('SP074',5,'BG-OMO-01',NULL,12,6),('SP075',5,'BG-OMO-02',NULL,20,10),
    ('SP076',5,'BG-OMOM-01',NULL,8,4),
    ('SP077',5,'BG-TIDE-01',NULL,15,6),('SP078',5,'BG-TIDEL-01',NULL,10,5),
    ('SP079',5,'BG-SURF-01',NULL,18,8),('SP080',5,'BG-SURF-02',NULL,25,10),
    -- Nước xả vải
    ('SP081',5,'XV-COMF-01',NULL,15,6),('SP082',5,'XV-COMF-02',NULL,12,6),
    ('SP083',5,'XV-DOWNY-01',NULL,12,6),('SP084',5,'XV-DOWNY-02',NULL,10,6),
    -- Nước rửa chén
    ('SP085',5,'RC-SUN-01',NULL,20,10),('SP086',5,'RC-SUN-02',NULL,18,10),
    ('SP087',5,'RC-JOY-01',NULL,15,8),
    -- Nước lau sàn & vệ sinh
    ('SP088',5,'LS-VIM-01',NULL,12,6),('SP089',5,'LS-VIM-02',NULL,10,6),
    ('SP090',5,'LS-VIM-03',NULL,15,8),('SP091',5,'LS-VIM-04',NULL,12,6),
    ('SP092',5,'LS-CIF-01',NULL,10,5),
    -- Vật dụng gia đình
    ('SP093',1,'DD-LY-01',NULL,20,10),('SP094',1,'DD-LYG-01',NULL,15,8),
    ('SP095',1,'DD-HOP-01',NULL,25,10),
    ('SP096',1,'DD-RO-01',NULL,15,5),('SP097',1,'DD-THUNG-01',NULL,8,3),
    ('SP098',1,'DD-KEO-01',NULL,20,8),('SP099',1,'DD-DAO-01',NULL,15,5),
    ('SP100',1,'DD-KEM-01',NULL,30,10),('SP101',1,'DD-THIA-01',NULL,12,5),
    -- Mì gói & miến
    ('SP102',1,'MI-HH-01',DATE '2027-06-01',120,48),('SP103',1,'MI-HH-02',DATE '2027-06-01',100,48),
    ('SP104',1,'MI-DN-01',DATE '2027-05-01',80,36),
    ('SP105',1,'MI-OMA-01',DATE '2027-07-01',60,24),('SP106',1,'MI-GDL-01',DATE '2027-06-01',50,20),
    -- Nước mắm & nước tương
    ('SP107',1,'NM-NAMG-01',NULL,20,8),('SP108',1,'NM-NAMG-02',NULL,15,6),
    ('SP109',1,'NT-TTT-01',NULL,18,8),
    ('SP110',1,'SC-MAS-01',DATE '2027-09-01',30,12),('SP111',1,'TC-CHOL-01',DATE '2027-10-01',25,10),
    -- Gia vị nêm
    ('SP112',1,'HN-KNORR-01',DATE '2027-08-01',25,10),('SP113',1,'HN-KNORR-02',DATE '2027-08-01',22,10),
    ('SP114',1,'BN-AJI-01',DATE '2028-01-01',30,12),('SP115',1,'BN-AJI-02',DATE '2028-01-01',20,8),
    ('SP116',1,'BC-HC-01',DATE '2027-11-01',35,15),('SP117',1,'BC-HC-02',DATE '2027-11-01',30,15),
    -- Dầu ăn
    ('SP118',1,'DAU-TA-01',DATE '2027-12-01',20,8),('SP119',1,'DAU-TA-02',DATE '2027-12-01',8,4),
    ('SP120',1,'DAU-NEP-01',DATE '2028-01-01',15,6),('SP121',1,'DAU-SIM-01',DATE '2028-01-01',18,8),
    -- Gạo, đường, muối
    ('SP122',1,'GAO-THOM-01',NULL,10,5),('SP123',1,'GAO-NN-01',NULL,8,5),
    ('SP124',1,'DUONG-01',NULL,25,10),('SP125',1,'MUOI-01',NULL,40,20),
    -- Xà phòng & dầu gội
    ('SP126',5,'XP-LIFE-01',NULL,40,15),('SP127',5,'XP-LIFE-02',NULL,15,8),
    ('SP128',5,'DG-CLEAR-01',NULL,12,6),('SP129',5,'DG-CLEAR-02',NULL,10,6),
    ('SP130',5,'DG-SUN-01',NULL,12,6),
    ('SP131',5,'DG-PANT-01',NULL,10,5),('SP132',5,'DG-HS-01',NULL,8,4),
    ('SP133',5,'DG-REJOICE-01',NULL,12,6),
    -- Sữa tắm
    ('SP134',5,'ST-LIFE-01',NULL,10,5),('SP135',5,'ST-DOVE-01',NULL,8,4),
    ('SP136',5,'ST-LUX-01',NULL,12,6),('SP137',5,'ST-REX-01',NULL,10,5),
    -- Kem đánh răng & bàn chải
    ('SP138',5,'KDR-CREST-01',NULL,20,8),('SP139',5,'KDR-PS-01',NULL,25,10),
    ('SP140',5,'KDR-PS-02',NULL,22,10),
    ('SP141',5,'BC-ORAL-01',NULL,30,12),('SP142',5,'BC-PS-01',NULL,35,15),
    -- Khăn giấy, tã & vệ sinh
    ('SP143',1,'KG-BOBBY-01',NULL,30,15),('SP144',1,'KG-BOBBY-02',NULL,20,10),
    ('SP145',1,'KG-BOBBY-03',NULL,25,10),('SP146',1,'KG-BOBBY-04',NULL,40,20),
    ('SP147',3,'TA-BOBBY-01',NULL,8,4),('SP148',3,'TA-BOBBY-02',NULL,6,4),
    ('SP149',5,'VS-KOTEX-01',NULL,25,10)
) AS t(sku, lid, bnum, exp, qty, mq)
JOIN Products p ON p.sku_code = t.sku;
