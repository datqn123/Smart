package com.example.smart_erp.catalog.service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.stream.Collectors;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import com.example.smart_erp.catalog.media.CloudinaryMediaService;

import com.fasterxml.jackson.databind.JsonNode;

import com.example.smart_erp.catalog.dto.ProductCreateRequest;
import com.example.smart_erp.catalog.dto.ProductsBulkDeleteRequest;
import com.example.smart_erp.catalog.repository.CategoryJdbcRepository;
import com.example.smart_erp.catalog.repository.ProductJdbcRepository;
import com.example.smart_erp.catalog.repository.ProductJdbcRepository.ProductDetailHeaderRow;
import com.example.smart_erp.catalog.repository.ProductJdbcRepository.ProductLockSnapshot;
import com.example.smart_erp.catalog.response.ProductBulkDeleteData;
import com.example.smart_erp.catalog.response.ProductCreatedData;
import com.example.smart_erp.catalog.response.ProductDeleteData;
import com.example.smart_erp.catalog.response.ProductDetailData;
import com.example.smart_erp.catalog.response.ProductListItemData;
import com.example.smart_erp.catalog.response.ProductListPageData;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;

import org.springframework.security.oauth2.jwt.Jwt;

@Service
public class ProductService {

	/** Tối đa số part {@code file} mỗi request — SRS §14.5 (OQ-7). */
	public static final int MAX_CREATE_IMAGE_FILES = 10;

	private final ProductJdbcRepository productJdbcRepository;
	private final CategoryJdbcRepository categoryJdbcRepository;
	private final CloudinaryMediaService cloudinaryMediaService;
	private final ProductImageService productImageService;
	private final ExecutorService productImageUploadExecutor;

	public ProductService(ProductJdbcRepository productJdbcRepository, CategoryJdbcRepository categoryJdbcRepository,
			CloudinaryMediaService cloudinaryMediaService, ProductImageService productImageService,
			@Qualifier("productImageUploadExecutor") ExecutorService productImageUploadExecutor) {
		this.productJdbcRepository = productJdbcRepository;
		this.categoryJdbcRepository = categoryJdbcRepository;
		this.cloudinaryMediaService = cloudinaryMediaService;
		this.productImageService = productImageService;
		this.productImageUploadExecutor = productImageUploadExecutor;
	}

	@Transactional(readOnly = true)
	public ProductListPageData list(String searchRaw, Integer categoryId, String statusRaw, int page, int limit,
			String sortRaw) {
		if (page < 1 || limit < 1 || limit > 100) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số phân trang không hợp lệ",
					Map.of("page", "page >= 1", "limit", "1–100"));
		}
		String orderBy;
		try {
			orderBy = ProductJdbcRepository.resolveListOrderBy(sortRaw);
		}
		catch (IllegalArgumentException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số sort không hợp lệ", Map.of("sort", "Giá trị không nằm trong whitelist"));
		}
		String status = normalizeListStatus(statusRaw);
		String search = searchRaw != null && !searchRaw.isBlank() ? searchRaw.trim() : null;
		long total = productJdbcRepository.countList(search, categoryId, status);
		int offset = (page - 1) * limit;
		List<ProductListItemData> items = productJdbcRepository.findListPage(search, categoryId, status, orderBy,
				limit, offset);
		return new ProductListPageData(items, page, limit, total);
	}

	private static String normalizeListStatus(String statusRaw) {
		if (statusRaw == null || statusRaw.isBlank()) {
			return "all";
		}
		String s = statusRaw.trim();
		if ("all".equalsIgnoreCase(s) || "Active".equals(s) || "Inactive".equals(s)) {
			return "all".equalsIgnoreCase(s) ? "all" : s;
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số status không hợp lệ");
	}

	@Transactional(readOnly = true)
	public Optional<Integer> findIdBySku(String skuCode) {
		if (skuCode == null || skuCode.isBlank()) {
			return Optional.empty();
		}
		return productJdbcRepository.findIdBySku(skuCode.trim());
	}

	@Transactional
	public ProductCreatedData create(ProductCreateRequest req) {
		String sku = req.skuCode().trim();
		if (productJdbcRepository.existsSku(sku)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Mã SKU đã tồn tại", Map.of("skuCode", "Trùng sku_code"));
		}
		Integer categoryId = req.categoryId();
		validateCategoryOptional(categoryId);
		String status = normalizeProductStatus(req.status());
		String barcode = normalizeBlankToNull(req.barcode());
		String imageUrl = normalizeBlankToNull(req.imageUrl());
		String description = req.description() == null ? null : req.description().trim();
		if (description != null && description.isEmpty()) {
			description = null;
		}
		BigDecimal weight = req.weight();
		LocalDate effDate = LocalDate.now();
		if (StringUtils.hasText(req.priceEffectiveDate())) {
			try {
				effDate = LocalDate.parse(req.priceEffectiveDate().trim());
			}
			catch (DateTimeParseException e) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "priceEffectiveDate không hợp lệ",
						Map.of("priceEffectiveDate", "Định dạng yyyy-MM-dd"));
			}
		}
		String baseUnit = req.baseUnitName().trim();
		int pid = productJdbcRepository.insertProduct(categoryId, sku, barcode, req.name().trim(), description, weight,
				status, imageUrl);
		int unitId = productJdbcRepository.insertBaseUnit(pid, baseUnit);
		productJdbcRepository.insertPriceHistory(pid, unitId, req.costPrice(), req.salePrice(), effDate);
		return toCreated(productJdbcRepository.findListItemById(pid).orElseThrow(
				() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc lại sản phẩm sau tạo")),
				unitId);
	}

	/**
	 * Tạo sản phẩm + upload nhiều ảnh song song (Cloudinary) rồi lưu gallery; nếu bất kỳ bước nào lỗi sau
	 * {@link #create}, xóa sản phẩm (all-or-nothing) — SRS §14.
	 */
	public ProductCreatedData createWithImageFiles(ProductCreateRequest req, List<MultipartFile> files,
			Integer primaryImageIndex) {
		if (files == null || files.isEmpty()) {
			return create(req);
		}
		if (files.size() > MAX_CREATE_IMAGE_FILES) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Quá nhiều file ảnh",
					Map.of("file", "Tối đa " + MAX_CREATE_IMAGE_FILES + " tệp mỗi lần tạo"));
		}
		int pIdx = primaryImageIndex != null ? primaryImageIndex : 0;
		if (pIdx < 0 || pIdx >= files.size()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "primaryImageIndex không hợp lệ",
					Map.of("primaryImageIndex", "0 .. " + (files.size() - 1)));
		}
		for (MultipartFile f : files) {
			cloudinaryMediaService.validateFile(f);
		}
		ProductCreatedData created = create(req);
		int pid = created.id();
		try {
			List<UploadIdx> parts = new ArrayList<>();
			List<CompletableFuture<UploadIdx>> futures = new ArrayList<>();
			for (int i = 0; i < files.size(); i++) {
				final int idx = i;
				MultipartFile mf = files.get(i);
				futures.add(CompletableFuture.supplyAsync(() -> {
					String url = cloudinaryMediaService.uploadProductImage(mf, pid);
					long size = mf.getSize() > 0 ? mf.getSize() : 0L;
					String mime = normalizeMimeForGallery(mf.getContentType());
					return new UploadIdx(idx, url, size, mime);
				}, productImageUploadExecutor));
			}
			for (CompletableFuture<UploadIdx> cf : futures) {
				parts.add(cf.join());
			}
			parts.sort(Comparator.comparingInt(UploadIdx::index));
			List<String> urls = parts.stream().map(UploadIdx::url).collect(Collectors.toList());
			List<Long> sizes = parts.stream().map(UploadIdx::fileSize).collect(Collectors.toList());
			List<String> mimes = parts.stream().map(UploadIdx::mime).collect(Collectors.toList());
			productImageService.persistGalleryAfterUploads(pid, urls, sizes, mimes, pIdx);
		}
		catch (RuntimeException e) {
			productJdbcRepository.deleteProduct(pid);
			if (e instanceof CompletionException ce) {
				Throwable c = ce.getCause();
				if (c instanceof BusinessException be) {
					throw be;
				}
			}
			throw e;
		}
		return toCreated(productJdbcRepository.findListItemById(pid).orElseThrow(
				() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc lại sản phẩm sau tạo ảnh")),
				created.unitId());
	}

	private record UploadIdx(int index, String url, long fileSize, String mime) {
	}

	private static String normalizeMimeForGallery(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		int semi = raw.indexOf(';');
		return semi > 0 ? raw.substring(0, semi).trim() : raw.trim();
	}

	private static ProductCreatedData toCreated(ProductListItemData row, int unitId) {
		return new ProductCreatedData(row.id(), row.skuCode(), row.barcode(), row.name(), row.categoryId(),
				row.categoryName(), row.imageUrl(), row.status(), row.currentStock(), row.currentPrice(),
				row.createdAt(), row.updatedAt(), unitId);
	}

	private void validateCategoryOptional(Integer categoryId) {
		if (categoryId == null) {
			return;
		}
		if (categoryId <= 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "categoryId không hợp lệ");
		}
		long cid = categoryId.longValue();
		if (!categoryJdbcRepository.existsCategoryRow(cid)) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, "Danh mục không tồn tại",
					Map.of("categoryId", String.valueOf(categoryId)));
		}
		if (!categoryJdbcRepository.existsActiveId(cid)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh mục không còn hiệu lực",
					Map.of("categoryId", String.valueOf(categoryId), "code", "INVALID_CATEGORY"));
		}
	}

	private static String normalizeProductStatus(String raw) {
		if (raw == null || raw.isBlank()) {
			return "Active";
		}
		String s = raw.trim();
		if ("Active".equals(s) || "Inactive".equals(s)) {
			return s;
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "status không hợp lệ");
	}

	private static String normalizeBlankToNull(String s) {
		if (s == null || s.isBlank()) {
			return null;
		}
		return s.trim();
	}

	@Transactional(readOnly = true)
	public ProductDetailData getById(int id) {
		ProductDetailHeaderRow h = productJdbcRepository.loadDetailHeader(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy sản phẩm"));
		return new ProductDetailData(h.id(), h.skuCode(), h.barcode(), h.name(), h.categoryId(), h.categoryName(),
				h.description(), h.weight(), h.status(), h.imageUrl(), h.createdAt(), h.updatedAt(),
				productJdbcRepository.listUnitsWithCurrentPrices(id),
				productJdbcRepository.listGalleryImages(id));
	}

	@Transactional
	public ProductDetailData patch(int id, JsonNode body) {
		if (body == null || !body.isObject() || body.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Body PATCH không được rỗng");
		}
		ProductLockSnapshot lock = productJdbcRepository.lockProductForUpdate(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy sản phẩm"));
		String sku = lock.skuCode();
		String barcode = lock.barcode();
		String name = lock.name();
		Integer categoryId = lock.categoryId();
		String description = lock.description();
		BigDecimal weight = lock.weight();
		String status = lock.status();
		String imageUrl = lock.imageUrl();
		boolean any = false;

		if (body.has("skuCode")) {
			JsonNode n = body.get("skuCode");
			if (!n.isNull()) {
				any = true;
				sku = requireText(n, "skuCode", 50);
				if (productJdbcRepository.existsOtherSku(id, sku)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Mã SKU đã tồn tại");
				}
			}
		}
		if (body.has("barcode")) {
			JsonNode n = body.get("barcode");
			any = true;
			if (n.isNull()) {
				barcode = null;
			}
			else {
				String t = n.asText().trim();
				if (t.isEmpty()) {
					barcode = null;
				}
				else if (t.length() > 100) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "barcode quá dài");
				}
				else {
					barcode = t;
				}
			}
		}
		if (body.has("name")) {
			JsonNode n = body.get("name");
			if (!n.isNull()) {
				any = true;
				name = requireText(n, "name", 255);
			}
		}
		if (body.has("categoryId")) {
			JsonNode n = body.get("categoryId");
			any = true;
			if (n.isNull()) {
				categoryId = null;
			}
			else {
				if (!n.isIntegralNumber()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "categoryId không hợp lệ");
				}
				int cid = n.asInt();
				if (cid <= 0) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "categoryId không hợp lệ");
				}
				validateCategoryOptional(cid);
				categoryId = cid;
			}
		}
		if (body.has("description")) {
			JsonNode n = body.get("description");
			any = true;
			if (n.isNull()) {
				description = null;
			}
			else {
				description = n.asText().trim();
				if (description.isEmpty()) {
					description = null;
				}
			}
		}
		if (body.has("weight")) {
			JsonNode n = body.get("weight");
			any = true;
			if (n.isNull()) {
				weight = null;
			}
			else if (n.isNumber()) {
				weight = n.decimalValue();
				if (weight.signum() < 0) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "weight không hợp lệ");
				}
			}
			else {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "weight không hợp lệ");
			}
		}
		if (body.has("status")) {
			JsonNode n = body.get("status");
			if (!n.isNull()) {
				any = true;
				status = normalizeProductStatus(n.asText());
			}
		}
		if (body.has("imageUrl")) {
			JsonNode n = body.get("imageUrl");
			any = true;
			if (n.isNull()) {
				imageUrl = null;
			}
			else {
				String t = n.asText().trim();
				if (t.isEmpty()) {
					imageUrl = null;
				}
				else if (t.length() > 500) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "imageUrl quá dài");
				}
				else {
					imageUrl = t;
				}
			}
		}

		boolean pricePair = body.hasNonNull("salePrice") && body.hasNonNull("costPrice");
		boolean pricePartial = body.has("salePrice") || body.has("costPrice");
		if (pricePartial && !pricePair) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Khi đổi giá, cần gửi cả salePrice và costPrice");
		}
		if (pricePair) {
			any = true;
			if (!body.get("salePrice").isNumber() || !body.get("costPrice").isNumber()) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Giá không hợp lệ");
			}
			BigDecimal sale = body.get("salePrice").decimalValue();
			BigDecimal cost = body.get("costPrice").decimalValue();
			if (sale.signum() < 0 || cost.signum() < 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Giá phải >= 0");
			}
			LocalDate eff = LocalDate.now();
			if (body.hasNonNull("priceEffectiveDate")) {
				try {
					eff = LocalDate.parse(body.get("priceEffectiveDate").asText().trim());
				}
				catch (DateTimeParseException e) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "priceEffectiveDate không hợp lệ");
				}
			}
			int unitId = productJdbcRepository.findBaseUnitId(id)
					.orElseThrow(() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Thiếu đơn vị cơ sở"));
			Optional<BigDecimal[]> latest = productJdbcRepository.findLatestEffectivePrices(id, unitId);
			boolean changed = latest.isEmpty() || latest.get()[0].compareTo(cost) != 0
					|| latest.get()[1].compareTo(sale) != 0;
			if (changed) {
				productJdbcRepository.insertPriceHistory(id, unitId, cost, sale, eff);
			}
		}

		if (!any) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một trường hợp lệ để cập nhật");
		}
		productJdbcRepository.updateProduct(id, sku, barcode, name, categoryId, description, weight, status, imageUrl);
		return getById(id);
	}

	private static String requireText(JsonNode n, String field, int maxLen) {
		String t = n.asText("").trim();
		if (t.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường không được để trống", Map.of(field, "Bắt buộc"));
		}
		if (t.length() > maxLen) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường quá dài", Map.of(field, "Tối đa " + maxLen));
		}
		return t;
	}

	@Transactional
	public ProductDeleteData delete(int id, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt, "Chỉ tài khoản Owner mới được xóa sản phẩm");
		productJdbcRepository.lockProductForUpdate(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy sản phẩm"));
		assertDeletableOrThrow(id);
		int n = productJdbcRepository.deleteProduct(id);
		if (n != 1) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Xóa sản phẩm không thành công");
		}
		return new ProductDeleteData(id, true);
	}

	@Transactional
	public ProductBulkDeleteData bulkDelete(ProductsBulkDeleteRequest req, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt, "Chỉ tài khoản Owner mới được xóa sản phẩm");
		List<Integer> ids = req.ids();
		Set<Integer> uniq = new HashSet<>(ids);
		if (uniq.size() != ids.size()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách ids không được trùng lặp");
		}
		for (int pid : ids) {
			if (!productJdbcRepository.existsProductId(pid)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "ids chứa sản phẩm không tồn tại",
						Map.of("invalidId", String.valueOf(pid)));
			}
		}
		for (int pid : ids) {
			Optional<String> reason = deleteBlockReason(pid);
			if (reason.isPresent()) {
				String r = reason.get();
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không thể xóa hết danh sách đã chọn. " + userMessageForDeleteBlockReason(r),
						Map.of("failedId", String.valueOf(pid), "reason", r));
			}
		}
		productJdbcRepository.lockProductsForUpdate(ids);
		int deleted = productJdbcRepository.deleteProducts(ids);
		if (deleted != ids.size()) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Xóa bulk không khớp số dòng");
		}
		return new ProductBulkDeleteData(new ArrayList<>(ids), deleted);
	}

	private void assertDeletableOrThrow(int productId) {
		deleteBlockReason(productId).ifPresent(r -> {
			throw new BusinessException(ApiErrorCode.CONFLICT, userMessageForDeleteBlockReason(r),
					Map.of("reason", r, "failedId", String.valueOf(productId)));
		});
	}

	/**
	 * Thông báo tiếng Việt cho người dùng; {@code details.reason} vẫn là mã máy (SRS / API).
	 */
	private static String userMessageForDeleteBlockReason(String reasonCode) {
		return switch (reasonCode) {
			case "HAS_STOCK_RECEIPT" -> "Sản phẩm đã xuất hiện trên ít nhất một phiếu nhập kho, không được xóa.";
			case "HAS_ORDER_LINES" -> "Sản phẩm đã xuất hiện trên ít nhất một đơn hàng, không được xóa.";
			case "HAS_STOCK" -> "Sản phẩm còn tồn kho (số lượng lớn hơn 0), không được xóa.";
			default -> "Sản phẩm không đủ điều kiện xóa.";
		};
	}

	private Optional<String> deleteBlockReason(int productId) {
		if (productJdbcRepository.existsStockReceiptDetail(productId)) {
			return Optional.of("HAS_STOCK_RECEIPT");
		}
		if (productJdbcRepository.existsOrderDetail(productId)) {
			return Optional.of("HAS_ORDER_LINES");
		}
		if (productJdbcRepository.sumInventoryQuantity(productId) > 0L) {
			return Optional.of("HAS_STOCK");
		}
		return Optional.empty();
	}

}
