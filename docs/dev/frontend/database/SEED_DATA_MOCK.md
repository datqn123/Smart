# Seed Data Mock - Cửa hàng Tạp hóa

> Dữ liệu mẫu thực tế cho tiệm tạp hóa bán bánh kẹo, nước giải khát, hóa phẩm, vật dụng gia đình, gia vị & thực phẩm khô, chăm sóc cá nhân.

---

## 1. Danh mục hàng hóa (Categories)

### Cấu trúc danh mục

```
Bánh kẹo & Snack
├── Bánh quy & bánh bông lan (bánh quy bơ, Oreo, Cosy, Solite, AFC, bánh gạo One One)
├── Kẹo các loại (kẹo cứng, kẹo mềm, kẹo dẻo, kẹo gum)
├── Snack (Poca, Lay's, Oishi, khoai tây chiên Slide)
├── Socola & bánh ngọt (KitKat, ChocoPie, Custas, bánh bông lan cuộn)
└── Bánh ăn dặm trẻ em (Cerelac, Growsure)

Nước giải khát
├── Nước ngọt có gas (Pepsi, 7Up, Mirinda, Coca-Cola, Sprite, Fanta)
├── Bia (Sài Gòn, 333, Tiger Budweiser)
├── Nước suối & nước tinh khiết (Aquafina, La Vie, Dasani)
├── Trà & cà phê (C2, Nescafe, trà lipton)
├── Sữa tươi & sữa chua (Vinamilk, Milo, sữa chua ăn)
└── Nước trái cây (cam ép Vinamilk)

Hóa phẩm & Tẩy rửa
├── Bột giặt & nước giặt (Omo, Tide, Surf, Lix, nước giặt OMO Matic)
├── Nước xả vải (Comfort, Downy)
├── Nước rửa chén (Sunlight, Joy, Cif)
├── Nước lau sàn & vệ sinh nhà cửa (Vim lau sàn, Vim lau kính, Vim tẩy nhà tắm, Cif)

Vật dụng gia đình
├── Ly chén dĩa & hộp đựng (ly nhựa, ly giấy, hộp nhựa Duy Tân)
├── Dao kéo dụng cụ bếp (kéo, dao, kềm, thìa dĩa Kềm Nghĩa)
├── Đồ nhựa gia dụng (rổ, thùng, soong nhựa Duy Tân)

Gia vị & Thực phẩm khô
├── Mì gói & miến (Hảo Hảo, Đệ Nhất, Goodle, Omachi)
├── Nước mắm & nước tương (Nam Ngư, Tam Thái Tử)
├── Hạt nêm & bột ngọt (Knorr, Ajinomoto, bột canh Hải Châu)
├── Dầu ăn (Tường An, Neptune, Simply)
├── Gạo (thơm, Nàng Nhen, Tài Nguyên)
└── Đường, muối, hạt nêm, gia vị khác

Chăm sóc cá nhân
├── Xà phòng & dầu gội (Lifebuoy, Clear, Sunsilk, Dove, Rejoice, Pantene)
├── Sữa tắm (Lifebuoy, Dove, Lux)
├── Kem đánh răng & bàn chải (Crest, PS, Oral-B, CloseUp)
├── Khăn giấy & tã (Bobby khăn ướt, giấy vệ sinh, khăn giấy mặt, tã quần Bobby)
├── Sản phẩm phụ nữ (băng vệ sinh Kotex, Laurier)
└── Xịt khử mùi (Rexona)

---

## 2. Nhà cung cấp (Suppliers)

### 2.1 Nhà cung cấp Bánh kẹo

| # | Nhà cung cấp | Chi tiết | Sản phẩm chính |
|:-:|-------------|---------|----------------|
| 1 | **Công ty CP Mondelez Kinh Đô Việt Nam** | Thương hiệu bánh kẹo số 1 Việt Nam (35% thị phần). Nhà máy tại KCN Biên Hòa, Đồng Nai. Sở hữu các nhãn: **Oreo, Cosy, Solite, AFC, Ritz, LU, Slide, Kinh Đô bánh trung thu**. | Bánh quy Oreo, Cosy kem sữa, Solite bông lan cuộn, AFC bơ tỏi, Ritz, Slide khoai tây, LU bơ thập cẩm, bánh gạo One One, bánh trung thu Kinh Đô |
| 2 | **Công ty CP Bánh kẹo Hải Hà** | Thành lập 1960, 10.000 tấn/năm. Trụ sở: 25-27 Trương Định, Hai Bà Trưng, Hà Nội. | Bánh quy bơ sữa, bánh quy socola, bánh kem xốp dâu, kẹo cứng trái cây, kẹo mềm sữa, bánh cracker, kẹo dẻo, kẹo Chew |
| 3 | **Công ty TNHH Thực phẩm Orion Vina** | Tập đoàn Hàn Quốc, nhà máy tại KCN Sóng Thần, Bình Dương. Sản phẩm nổi bật nhất là ChocoPie. | ChocoPie, Custas, bánh quy Orion bơ sữa, bánh xốp Orion vị dâu kem, ChocoPie hộp quà |
| 4 | **Công ty CP Bibica** | Nhà máy tại Long An. Nổi tiếng với bánh bông lan Hura, kẹo socola. | Bánh bông lan cuộn Hura (bơ sữa, cam, cốm), bánh ăn dặm Growsure, kẹo socola Bibica |
| 5 | **Công ty TNHH Nestlé Việt Nam** | Tập đoàn Thụy Sĩ, nhà máy tại Đồng Nai. Mảng bánh kẹo gồm KitKat, kẹo cao su, bánh ăn dặm. | KitKat 4 thanh, kẹo cao su Doublemint, bánh ăn dặm Cerelac (gạo, lúa mạch), socola Smarties |
| 6 | **Công ty CP Bánh kẹo Tràng An** | Nhà máy tại Hà Nội. Bánh trung thu, bánh quy, bánh kem xốp các loại. | Bánh trung thu Tràng An, bánh quy, bánh kem xốp, kẹo lạc, kẹo vừng |
| 7 | **Công ty CP Bánh kẹo Biển Xanh** | Thương hiệu mới chuyển đổi từ Hải Hà, tập trung bánh snack. | Snack Biển Xanh, bánh gạo lứt, bánh ăn kiêng |

### 2.2 Nhà cung cấp Nước giải khát

| # | Nhà cung cấp | Chi tiết | Sản phẩm chính |
|:-:|-------------|---------|----------------|
| 8 | **Công ty TNHH Nước giải khát Suntory PepsiCo Việt Nam** | Liên doanh Nhật-Mỹ, nhà máy tại Bình Dương và Hà Nội. | Pepsi, 7Up, Mirinda (cam, nho), Aquafina, Sting, Pepsi không calo |
| 9 | **Công ty TNHH Nước giải khát Coca-Cola Việt Nam** | Nhà máy tại Hà Nội, Đà Nẵng, TP.HCM. | Coca-Cola, Sprite, Fanta, Dasani, Minute Maid, Thực phẩm C2 (liên doanh) |
| 10 | **Công ty CP Sữa Việt Nam (Vinamilk)** | Số 1 ngành sữa, trụ sở TP.HCM. | Sữa tươi (có đường/không đường) 1L, sữa chua ăn, sữa chua uống, nước ép cam, sữa bột Dielac |
| 11 | **Tập đoàn Masan** | Công ty đa ngành, mảng nước uống: **C2 trà xanh**, các loại đồ uống. | Trà xanh C2 chai 1.5L/500ml, C2 hũ, trà sữa xanh C2 |
| 12 | **Công ty TNHH Nestlé Việt Nam** | Phân phối Milo, La Vie, Nescafe. | Milo hộp 180ml/115ml, La Vie 1.5L/500ml, Nescafe hòa tan, Nescafe sữa |
| 13 | **Công ty CP Bia Sài Gòn (Sabeco)** | Tổng công ty bia lớn nhất Việt Nam. | Bia Sài Gòn lager, Bia 333, bia Sài Gòn Special, Bia Saigon Chill |

### 2.3 Nhà cung cấp Hóa phẩm & Tẩy rửa

| # | Nhà cung cấp | Chi tiết | Sản phẩm chính |
|:-:|-------------|---------|----------------|
| 14 | **Công ty TNHH Quốc tế Unilever Việt Nam** | Tập đoàn Anh-Hà Lan, nhà máy tại Củ Chi, TP.HCM. Chiếm 71% thị phần hóa phẩm cùng P&G. | **Omo** (bột giặt/nước giặt), **Comfort** (nước xả), **Sunlight** (rửa chén), **Vim** (lau sàn, lau kính, tẩy nhà tắm), **Cif** (nước tẩy bếp), **Surf** (bột giặt) |
| 15 | **Công ty TNHH P&G Việt Nam** | Tập đoàn Mỹ, nhà máy tại Bình Dương. Cạnh tranh trực tiếp với Unilever. | **Tide** (bột giặt), **Downy** (nước xả), **Ariel** (nước giặt), **Joy** (rửa chén), **Mr. Clean** (lau sàn, lau bếp) |

### 2.4 Nhà cung cấp Vật dụng gia đình

| # | Nhà cung cấp | Chi tiết | Sản phẩm chính |
|:-:|-------------|---------|----------------|
| 16 | **Công ty CP Nhựa Duy Tân** | Nhà sản xuất nhựa số 1 Việt Nam, trụ sở Bình Tân, TP.HCM. | Ly nhựa, ly giấy, hộp nhựa, rổ nhựa, thùng nhựa, soong nhựa, ghế nhựa |
| 17 | **Công ty CP Kềm Nghĩa** | Thương hiệu dao kéo nổi tiếng Việt Nam từ Bình Dương. | Kéo inox, dao inox, kềm bấm móng, bộ thìa dĩa inox, bộ đồ ăn gia đình |

### 2.5 Nhà cung cấp Gia vị & Thực phẩm khô

| # | Nhà cung cấp | Chi tiết | Sản phẩm chính |
|:-:|-------------|---------|----------------|
| 18 | **Công ty CP Acecook Việt Nam** | Nhà sản xuất mì gói lớn nhất Việt Nam, nhà máy tại Bình Chánh, TP.HCM. | Mì Hảo Hảo (tôm chua cay, sườn heo), mì Đệ Nhất, miến Goodle, phở Goodle, mì Omachi |
| 19 | **Tập đoàn Masan (Masan Consumer)** | Thị trường số 1 ngành gia vị với các thương hiệu. | Nước mắm Nam Ngư, nước tương Tam Thái Tử, hạt nêm Knorr, bột ngọt Ajinomoto (phân phối), sốt cà Masan, bột canh Hải Châu, chao, tương ớt Cholimex |
| 20 | **Công ty CP Dầu thực vật Tường An** | Nhà máy tại Biên Hòa, Đồng Nai. | Dầu Tường An 1L/5L, dầu Neptuna, dầu Simply, dầu Cái Lân |
| 21 | **Nhà phân phối Bách Hóa Xanh** | Chuỗi cửa hàng thực phẩm sạch, tự doanh gạo/đường. | Gạo thơm, gạo Nàng Nhen, đường cát trắng, muối iot |

### 2.6 Nhà cung cấp Chăm sóc cá nhân

| # | Nhà cung cấp | Chi tiết | Sản phẩm chính |
|:-:|-------------|---------|----------------|
| 22 | **Công ty TNHH Quốc tế Unilever Việt Nam** | Mảng chăm sóc cá nhân. | **Lifebuoy** (xà phòng, sữa tắm), **Clear** (dầu gội), **Sunsilk** (dầu gội), **Dove** (sữa tắm, dầu gội), **Rexona** (lăn khử mùi), **P/S** (kem đánh răng, bàn chải), **Lux** (sữa tắm) |
| 23 | **Công ty TNHH P&G Việt Nam** | Mảng chăm sóc cá nhân. | **Pantene** (dầu gội), **Head & Shoulders** (dầu gội), **Rejoice** (dầu gội), **Oral-B** (bàn chải), **Crest** (kem đánh răng), **Kotex** (băng vệ sinh) |
| 24 | **Công ty TNHH Giấy Tân Tiến** | Nhà sản xuất giấy lớn nhất Việt Nam (Bobby, Pull-Ups). | **Bobby** (khăn giấy ướt, giấy vệ sinh cuộn, khăn giấy mặt, khăn giấy ăn, tã quần Bobby) |

---

## 3. Danh sách sản phẩm chi tiết

### 3.1 Bánh kẹo & Snack

#### Nhóm bánh quy & bánh bông lan

| STT | Tên sản phẩm | Dung tích/Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:------------------:|:------------:|:-------:|:----------:|
| 1 | Bánh Oreo vị kem vani 134g | Gói 134g | Mondelez Kinh Đô | 10.000đ | 15.000đ |
| 2 | Bánh Oreo vị kem socola 134g | Gói 134g | Mondelez Kinh Đô | 10.000đ | 15.000đ |
| 3 | Bánh Cosy vị kem sữa 144g | Gói 144g | Mondelez Kinh Đô | 7.500đ | 11.000đ |
| 4 | Bánh Cosy vị socola 144g | Gói 144g | Mondelez Kinh Đô | 7.500đ | 11.000đ |
| 5 | Bánh Solite bông lan cuộn kem dâu 360g | Hộp 360g | Mondelez Kinh Đô | 25.000đ | 35.000đ |
| 6 | Bánh Solite bông lan cuộn kem lá dứa 360g | Hộp 360g | Mondelez Kinh Đô | 25.000đ | 35.000đ |
| 7 | Bánh AFC vị bơ tỏi 200g | Gói 200g | Mondelez Kinh Đô | 8.000đ | 12.000đ |
| 8 | Bánh Ritz hương phô mai 147g | Gói 147g | Mondelez Kinh Đô | 14.000đ | 20.000đ |
| 9 | Bánh gạo One One vị rong biển 100g | Gói 100g | Mondelez Kinh Đô | 5.000đ | 7.500đ |
| 10 | Bánh LU Pháp bơ thập cẩm 400g | Hộp thiếc 400g | Mondelez Kinh Đô | 85.000đ | 115.000đ |
| 11 | Bánh quy Hải Hà bơ sữa 200g | Gói 200g | Bánh kẹo Hải Hà | 8.500đ | 12.000đ |
| 12 | Bánh quy Hải Hà socola 200g | Gói 200g | Bánh kẹo Hải Hà | 9.000đ | 13.000đ |
| 13 | Bánh kem xốp Hải Hà vị dâu 150g | Gói 150g | Bánh kẹo Hải Hà | 6.500đ | 9.500đ |
| 14 | Bánh kem xốp Hải Hà vị socola 150g | Gói 150g | Bánh kẹo Hải Hà | 6.500đ | 9.500đ |
| 15 | Bánh quy Hải Hà lúa mạch 200g | Gói 200g | Bánh kẹo Hải Hà | 8.000đ | 12.000đ |
| 16 | Bánh bông lan cuộn kem Hura bơ sữa 360g | Hộp 360g | Bibica | 22.000đ | 32.000đ |
| 17 | Bánh bông lan cuộn kem Hura cam 360g | Hộp 360g | Bibica | 22.000đ | 32.000đ |
| 18 | Bánh bông lan cuộn kem Hura cốm 360g | Hộp 360g | Bibica | 22.000đ | 32.000đ |

#### Nhóm kẹo

| STT | Tên sản phẩm | Dung tích/Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:------------------:|:------------:|:-------:|:----------:|
| 19 | Kẹo cứng Hải Hà vị trái cây 300g | Túi 300g | Bánh kẹo Hải Hà | 12.000đ | 18.000đ |
| 20 | Kẹo mềm Hải Hà vị sữa 200g | Túi 200g | Bánh kẹo Hải Hà | 10.000đ | 15.000đ |
| 21 | Kẹo dẻo Hải Hà vị trái cây 200g | Túi 200g | Bánh kẹo Hải Hà | 11.000đ | 16.000đ |
| 22 | Kẹo Chew Hải Hà vị dâu 140g | Túi 140g | Bánh kẹo Hải Hà | 9.000đ | 14.000đ |
| 23 | Kẹo dẻo Kido vị trái cây 100g | Túi 100g | Kido | 6.000đ | 9.000đ |
| 24 | Kẹo dẻo Kido vị sữa 100g | Túi 100g | Kido | 6.000đ | 9.000đ |

#### Nhóm Socola & bánh ngọt

| STT | Tên sản phẩm | Dung tích/Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:------------------:|:------------:|:-------:|:----------:|
| 25 | Socola KitKat 4 thanh 42g | Gói 42g | Nestlé | 7.500đ | 11.000đ |
| 26 | Kẹo cao su Doublemint 12 viên | Vỉ 12 viên | Nestlé | 4.000đ | 6.000đ |
| 27 | ChocoPie Orion 336g (12 cái) | Hộp 336g | Orion Vina | 28.000đ | 39.000đ |
| 28 | Custas Orion vị trứng 288g | Hộp 288g | Orion Vina | 25.000đ | 35.000đ |
| 29 | Custas Orion vị socola 288g | Hộp 288g | Orion Vina | 25.000đ | 35.000đ |
| 30 | Bánh xốp Orion dâu kem 216g | Hộp 216g | Orion Vina | 22.000đ | 32.000đ |
| 31 | Bánh ăn dặm Cerelac Nestlé gạo 200g | Hộp 200g | Nestlé | 25.000đ | 35.000đ |
| 32 | Bánh ăn dặm Growsure Bibica 168g | Hộp 168g | Bibica | 18.000đ | 25.000đ |

#### Nhóm Snack

| STT | Tên sản phẩm | Dung tích/Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:------------------:|:------------:|:-------:|:----------:|
| 33 | Snack Poca vị tôm cay 85g | Gói 85g | PepsiCo | 5.500đ | 8.000đ |
| 34 | Snack Poca vị phô mai 85g | Gói 85g | PepsiCo | 5.500đ | 8.000đ |
| 35 | Snack Lay's vị tự nhiên 52g | Gói 52g | PepsiCo | 4.500đ | 7.000đ |
| 36 | Snack Lay's vị thịt nướng 52g | Gói 52g | PepsiCo | 4.500đ | 7.000đ |
| 37 | Snack Oishi vị tàu hủ ky 100g | Gói 100g | PepsiCo | 5.000đ | 8.000đ |
| 38 | Bánh gòn Oishi đường đen 120g | Gói 120g | PepsiCo | 6.000đ | 9.000đ |
| 39 | Snack khoai tây Slide vị tự nhiên 90g | Hộp 90g | Mondelez Kinh Đô | 10.000đ | 15.000đ |

### 3.2 Nước giải khát

#### Nước ngọt có gas

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 40 | Pepsi cola lon 330ml | Lon 330ml | PepsiCo | 5.000đ | 8.000đ |
| 41 | Pepsi cola chai 600ml | Chai 600ml | PepsiCo | 6.500đ | 10.000đ |
| 42 | Pepsi không calo lon 330ml | Lon 330ml | PepsiCo | 5.000đ | 8.000đ |
| 43 | 7Up lon 330ml | Lon 330ml | PepsiCo | 5.000đ | 8.000đ |
| 44 | Mirinda vị cam lon 330ml | Lon 330ml | PepsiCo | 5.000đ | 8.000đ |
| 45 | Mirinda vị nho lon 330ml | Lon 330ml | PepsiCo | 5.000đ | 8.000đ |
| 46 | Sting vàng lon 330ml | Lon 330ml | PepsiCo | 6.000đ | 9.000đ |
| 47 | Coca-Cola lon 330ml | Lon 330ml | Coca-Cola | 5.000đ | 8.000đ |
| 48 | Coca-Cola chai 600ml | Chai 600ml | Coca-Cola | 6.500đ | 10.000đ |
| 49 | Sprite lon 330ml | Lon 330ml | Coca-Cola | 5.000đ | 8.000đ |
| 50 | Fanta cam lon 330ml | Lon 330ml | Coca-Cola | 5.000đ | 8.000đ |

#### Bia

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 51 | Bia Sài Gòn lager lon 330ml | Lon 330ml | Sabeco | 6.500đ | 10.000đ |
| 52 | Bia 333 lon 330ml | Lon 330ml | Sabeco | 6.000đ | 9.500đ |
| 53 | Bia Sài Gòn Special lon 330ml | Lon 330ml | Sabeco | 7.000đ | 11.000đ |
| 54 | Bia Sài Gòn chai 355ml | Chai 355ml | Sabeco | 7.500đ | 11.500đ |

#### Nước suối & nước tinh khiết

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 55 | Aquafina chai 1.5L | Chai 1.5L | PepsiCo | 5.000đ | 8.000đ |
| 56 | Aquafina chai 500ml | Chai 500ml | PepsiCo | 3.000đ | 5.000đ |
| 57 | La Vie chai 1.5L | Chai 1.5L | Nestlé | 4.000đ | 6.500đ |
| 58 | La Vie chai 500ml | Chai 500ml | Nestlé | 2.500đ | 4.000đ |
| 59 | Dasani chai 1.5L | Chai 1.5L | Coca-Cola | 4.000đ | 6.500đ |

#### Trà & cà phê

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 60 | Trà xanh C2 chai 1.5L | Chai 1.5L | Masan | 8.000đ | 12.000đ |
| 61 | Trà xanh C2 chai 500ml | Chai 500ml | Masan | 4.500đ | 7.000đ |
| 62 | Trà sữa xanh C2 hũ 300ml | Hũ 300ml | Masan | 6.000đ | 9.000đ |
| 63 | Cà phê Nescafe hòa tan 100g | Hộp 100g | Nestlé | 30.000đ | 42.000đ |
| 64 | Nescafe sữa hòa tan 120g | Hộp 120g | Nestlé | 28.000đ | 40.000đ |

#### Sữa & nước trái cây

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 65 | Sữa tươi Vinamilk không đường 1L | Hộp 1L | Vinamilk | 20.000đ | 28.000đ |
| 66 | Sữa tươi Vinamilk có đường 1L | Hộp 1L | Vinamilk | 20.000đ | 28.000đ |
| 67 | Sữa tươi Vinamilk ít đường 1L | Hộp 1L | Vinamilk | 20.000đ | 28.000đ |
| 68 | Sữa chua Vinamilk ăn đường trắng 100g (4 hộp) | Lốc 4 hộp | Vinamilk | 10.000đ | 15.000đ |
| 69 | Sữa chua Vinamilk ăn không đường 100g (4 hộp) | Lốc 4 hộp | Vinamilk | 10.000đ | 15.000đ |
| 70 | Sữa chua uống Vinamilk 180ml (4 hộp) | Lốc 4 hộp | Vinamilk | 12.000đ | 18.000đ |
| 71 | Nước cam ép Vinamilk 1L | Hộp 1L | Vinamilk | 18.000đ | 25.000đ |
| 72 | Milo hộp 180ml | Hộp 180ml | Nestlé | 5.500đ | 8.000đ |
| 73 | Milo hộp 115ml | Hộp 115ml | Nestlé | 3.500đ | 5.500đ |

### 3.3 Hóa phẩm & Tẩy rửa

#### Bột giặt & nước giặt

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 74 | Bột giặt Omo công thức xanh 1.8kg | Túi 1.8kg | Unilever | 55.000đ | 75.000đ |
| 75 | Bột giặt Omo công thức xanh 800g | Túi 800g | Unilever | 28.000đ | 40.000đ |
| 76 | Nước giặt OMO Matic hương oải hương 3.8kg | Túi 3.8kg | Unilever | 100.000đ | 138.000đ |
| 77 | Bột giặt Tide 1.2kg | Túi 1.2kg | P&G | 45.000đ | 62.000đ |
| 78 | Nước giặt Tide thơm 1.36L | Chai 1.36L | P&G | 50.000đ | 68.000đ |
| 79 | Bột giặt Surf hương nước xả 2kg | Túi 2kg | Unilever | 38.000đ | 52.000đ |
| 80 | Bột giặt Surf 800g | Túi 800g | Unilever | 18.000đ | 26.000đ |

#### Nước xả vải

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 81 | Nước xả Comfort hương nước hoa 2L | Chai 2L | Unilever | 45.000đ | 62.000đ |
| 82 | Nước xả Comfort hương thiên nhiên 2L | Chai 2L | Unilever | 45.000đ | 62.000đ |
| 83 | Nước xả Downy hương nước hoa Pháp 2L | Chai 2L | P&G | 50.000đ | 68.000đ |
| 84 | Nước xả Downy hương oải hương 2L | Chai 2L | P&G | 50.000đ | 68.000đ |

#### Nước rửa chén

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 85 | Nước rửa chén Sunlight chanh 750ml | Chai 750ml | Unilever | 20.000đ | 30.000đ |
| 86 | Nước rửa chén Sunlight thiên nhiên 750ml | Chai 750ml | Unilever | 22.000đ | 32.000đ |
| 87 | Nước rửa chén Joy tinh chất chanh 700ml | Chai 700ml | P&G | 22.000đ | 32.000đ |

#### Nước lau sàn & vệ sinh

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 88 | Nước lau sàn Vim hương thiên nhiên 2L | Chai 2L | Unilever | 30.000đ | 42.000đ |
| 89 | Nước lau sàn Vim hoa oải hương 2L | Chai 2L | Unilever | 30.000đ | 42.000đ |
| 90 | Nước lau kính Vim 500ml | Chai 500ml | Unilever | 18.000đ | 26.000đ |
| 91 | Xịt tẩy vệ sinh Vim nhà tắm 500ml | Chai 500ml | Unilever | 22.000đ | 32.000đ |
| 92 | Nước tẩy bếp Cif 500ml | Chai 500ml | Unilever | 25.000đ | 35.000đ |

### 3.4 Vật dụng gia đình

| STT | Tên sản phẩm | Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:--------:|:------------:|:-------:|:----------:|
| 93 | Ly nhựa Duy Tân trong suốt 250ml (50 cái) | Bịch 50 cái | Duy Tân | 30.000đ | 42.000đ |
| 94 | Ly giấy Duy Tân 200ml (50 cái) | Bịch 50 cái | Duy Tân | 25.000đ | 35.000đ |
| 95 | Hộp nhựa Duy Tân tròn 1.5L có nắp | Cái | Duy Tân | 22.000đ | 32.000đ |
| 96 | Rổ nhựa Duy Tân đa năng cỡ vừa | Cái | Duy Tân | 15.000đ | 22.000đ |
| 97 | Thùng nhựa Duy Tân 60L có nắp | Cái | Duy Tân | 80.000đ | 110.000đ |
| 98 | Kéo inox Kềm Nghĩa 20cm cán nhựa | Cái | Kềm Nghĩa | 25.000đ | 35.000đ |
| 99 | Dao inox Kềm Nghĩa lưỡi lớn (20cm) | Cái | Kềm Nghĩa | 35.000đ | 50.000đ |
| 100 | Kềm bấm móng Kềm Nghĩa inox | Cái | Kềm Nghĩa | 18.000đ | 28.000đ |
| 101 | Bộ thìa dĩa inox Kềm Nghĩa (12 món) | Bộ 12 món | Kềm Nghĩa | 28.000đ | 40.000đ |

### 3.5 Gia vị & Thực phẩm khô

#### Mì gói & miến

| STT | Tên sản phẩm | Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:--------:|:------------:|:-------:|:----------:|
| 102 | Mì Hảo Hảo tôm chua cay 75g | Gói 75g | Acecook | 2.500đ | 3.500đ |
| 103 | Mì Hảo Hảo sườn heo 75g | Gói 75g | Acecook | 2.500đ | 3.500đ |
| 104 | Mì Đệ Nhất tôm 75g | Gói 75g | Acecook | 2.000đ | 3.000đ |
| 105 | Mì Omachi tôm hùm 90g | Gói 90g | Acecook | 4.000đ | 6.000đ |
| 106 | Miến Goodle 60g | Gói 60g | Acecook | 3.000đ | 4.500đ |

#### Nước mắm & nước tương

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 107 | Nước mắm Nam Ngư 500ml | Chai 500ml | Masan | 15.000đ | 22.000đ |
| 108 | Nước mắm Nam Ngư 1L | Chai 1L | Masan | 25.000đ | 35.000đ |
| 109 | Nước tương Tam Thái Tử 500ml | Chai 500ml | Masan | 12.000đ | 18.000đ |
| 110 | Sốt cà chua Masan 340g | Gói 340g | Masan | 8.000đ | 12.500đ |
| 111 | Tương ớt Cholimex 250g | Chai 250g | Masan | 7.000đ | 11.000đ |

#### Gia vị nêm

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 112 | Hạt nêm Knorr từ thịt thăn 400g | Túi 400g | Masan (Knorr) | 18.000đ | 25.000đ |
| 113 | Hạt nêm Knorr gà 400g | Túi 400g | Masan (Knorr) | 18.000đ | 25.000đ |
| 114 | Bột ngọt Ajinomoto 200g | Túi 200g | Masan (Ajinomoto) | 12.000đ | 17.000đ |
| 115 | Bột ngọt Ajinomoto 500g | Túi 500g | Masan (Ajinomoto) | 25.000đ | 35.000đ |
| 116 | Bột canh Hải Châu 200g | Gói 200g | Masan | 6.000đ | 10.000đ |
| 117 | Bột canh Hải Châu iot 200g | Gói 200g | Masan | 6.500đ | 10.500đ |

#### Dầu ăn

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 118 | Dầu ăn Tường An 1L | Chai 1L | Tường An | 25.000đ | 35.000đ |
| 119 | Dầu ăn Tường An 5L | Can 5L | Tường An | 100.000đ | 140.000đ |
| 120 | Dầu ăn Neptuna 1L | Chai 1L | Tường An | 28.000đ | 40.000đ |
| 121 | Dầu ăn Simply 1L | Chai 1L | Tường An | 22.000đ | 32.000đ |

#### Gạo & đường muối

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 122 | Gạo thơm 5kg | Túi 5kg | BHX | 55.000đ | 75.000đ |
| 123 | Gạo Nàng Nhen 5kg | Túi 5kg | BHX | 65.000đ | 90.000đ |
| 124 | Đường cát trắng tinh luyện 1kg | Túi 1kg | BHX | 12.000đ | 17.000đ |
| 125 | Muối iot 500g | Túi 500g | BHX | 3.000đ | 5.000đ |

### 3.6 Chăm sóc cá nhân

#### Xà phòng & dầu gội

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 126 | Xà phòng Lifebuoy diệt khuẩn 90g | Bánh 90g | Unilever | 6.500đ | 10.000đ |
| 127 | Xà phòng Lifebuoy bộ 3 bánh 90g x3 | Hộp 3 bánh | Unilever | 17.000đ | 25.000đ |
| 128 | Dầu gội Clear ngăn rụng tóc 360ml | Chai 360ml | Unilever | 45.000đ | 62.000đ |
| 129 | Dầu gội Clear mát lạnh 360ml | Chai 360ml | Unilever | 45.000đ | 62.000đ |
| 130 | Dầu gội Sunsilk mềm mượt 360ml | Chai 360ml | Unilever | 40.000đ | 56.000đ |
| 131 | Dầu gội Pantene suôn mượt 360ml | Chai 360ml | P&G | 48.000đ | 66.000đ |
| 132 | Dầu gội Head & Shoulders gàu 360ml | Chai 360ml | P&G | 50.000đ | 68.000đ |
| 133 | Dầu gội Rejoice mượt tóc 360ml | Chai 360ml | P&G | 42.000đ | 58.000đ |

#### Sữa tắm

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 134 | Sữa tắm Lifebuoy diệt khuẩn 450ml | Chai 450ml | Unilever | 38.000đ | 55.000đ |
| 135 | Sữa tắm Dove dưỡng ẩm 500ml | Chai 500ml | Unilever | 50.000đ | 70.000đ |
| 136 | Sữa tắm Lux quyến rũ 450ml | Chai 450ml | Unilever | 35.000đ | 50.000đ |
| 137 | Lăn khử mùi Rexona xịt 50ml | Chai 50ml | Unilever | 28.000đ | 40.000đ |

#### Kem đánh răng & bàn chải

| STT | Tên sản phẩm | Dung tích | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:---------:|:------------:|:-------:|:----------:|
| 138 | Kem đánh răng Crest trắng răng 120g | Tuýp 120g | P&G | 18.000đ | 28.000đ |
| 139 | Kem đánh răng P/S chống sâu răng 120g | Tuýp 120g | Unilever | 12.000đ | 18.000đ |
| 140 | Kem đánh răng P/S trắng răng 120g | Tuýp 120g | Unilever | 13.000đ | 20.000đ |
| 141 | Bàn chải đánh răng Oral-B mềm | Cái | P&G | 15.000đ | 22.000đ |
| 142 | Bàn chải đánh răng P/S | Cái | Unilever | 8.000đ | 12.000đ |

#### Khăn giấy, tã & sản phẩm vệ sinh

| STT | Tên sản phẩm | Quy cách | Nhà sản xuất | Giá vốn | Giá bán lẻ |
|:---:|-------------|:--------:|:------------:|:-------:|:----------:|
| 143 | Khăn giấy ướt Bobby 80 tờ | Hộp 80 tờ | Tân Tiến | 10.000đ | 15.000đ |
| 144 | Giấy vệ sinh Bobby cuộn 4 cuộn | Bịch 4 cuộn | Tân Tiến | 18.000đ | 28.000đ |
| 145 | Khăn giấy mặt Bobby cao cấp 100 tờ | Hộp 100 tờ | Tân Tiến | 8.000đ | 12.000đ |
| 146 | Khăn giấy ăn Bobby 200 tờ | Bịch 200 tờ | Tân Tiến | 5.000đ | 8.000đ |
| 147 | Tã quần Bobby size M (6-11kg) 42 cái | Bịch 42 cái | Tân Tiến | 85.000đ | 120.000đ |
| 148 | Tã quần Bobby size L (9-14kg) 36 cái | Bịch 36 cái | Tân Tiến | 88.000đ | 125.000đ |
| 149 | Băng vệ sinh Kotex trung bình 10 miếng | Gói 10 miếng | P&G | 18.000đ | 25.000đ |

---

## 4. Thống kê tổng quan

| Hạng mục | Số lượng |
|----------|:--------:|
| Danh mục cấp 1 (nhóm chính) | 6 |
| Danh mục cấp 2 (nhóm phụ) | 22 |
| Nhà cung cấp | 24 |
| Tổng sản phẩm | 149 |

### Phân bố theo danh mục

| Danh mục | Số SP | Nhà cung cấp chính |
|----------|:-----:|-------------------|
| Bánh quy & bánh bông lan | 18 | Mondelez Kinh Đô, Hải Hà, Bibica |
| Kẹo các loại | 6 | Hải Hà, Kido |
| Socola & bánh ngọt | 8 | Nestlé, Orion, Bibica |
| Snack | 7 | PepsiCo, Mondelez Kinh Đô |
| Nước ngọt có gas | 11 | PepsiCo, Coca-Cola |
| Bia | 4 | Sabeco |
| Nước suối | 5 | PepsiCo, Nestlé, Coca-Cola |
| Trà & cà phê | 5 | Masan, Nestlé |
| Sữa & nước trái cây | 9 | Vinamilk, Nestlé |
| Bột giặt & nước giặt | 7 | Unilever, P&G |
| Nước xả vải | 4 | Unilever, P&G |
| Nước rửa chén | 3 | Unilever, P&G |
| Nước lau sàn & vệ sinh | 5 | Unilever |
| Vật dụng gia đình | 9 | Duy Tân, Kềm Nghĩa |
| Mì gói & miến | 5 | Acecook |
| Nước mắm & nước tương | 5 | Masan |
| Gia vị nêm | 6 | Masan (Knorr, Ajinomoto) |
| Dầu ăn | 4 | Tường An |
| Gạo & đường muối | 4 | Bách Hóa Xanh |
| Xà phòng & dầu gội | 8 | Unilever, P&G |
| Sữa tắm | 4 | Unilever |
| Kem đánh răng & bàn chải | 5 | P&G, Unilever |
| Khăn giấy, tã & vệ sinh | 7 | Tân Tiến, P&G |
| **Tổng** | **149** | **24 NCC** |
