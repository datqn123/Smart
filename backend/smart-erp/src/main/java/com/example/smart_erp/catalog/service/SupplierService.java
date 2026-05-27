package com.example.smart_erp.catalog.service;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.fasterxml.jackson.databind.JsonNode;

import com.example.smart_erp.catalog.dto.SupplierCreateRequest;
import com.example.smart_erp.catalog.dto.SuppliersBulkDeleteRequest;
import com.example.smart_erp.catalog.repository.SupplierJdbcRepository;
import com.example.smart_erp.catalog.repository.SupplierJdbcRepository.SupplierLockRow;
import com.example.smart_erp.catalog.response.SupplierBulkDeleteData;
import com.example.smart_erp.catalog.response.SupplierDeleteData;
import com.example.smart_erp.catalog.response.SupplierDetailData;
import com.example.smart_erp.catalog.response.SupplierListItemData;
import com.example.smart_erp.catalog.response.SupplierListPageData;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;

import org.springframework.security.oauth2.jwt.Jwt;

@Service
public class SupplierService {

	private static final Pattern EMAIL_PATTERN = Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");

	private final SupplierJdbcRepository supplierJdbcRepository;

	public SupplierService(SupplierJdbcRepository supplierJdbcRepository) {
		this.supplierJdbcRepository = supplierJdbcRepository;
	}

	@Transactional(readOnly = true)
	public SupplierListPageData list(String searchRaw, String statusRaw, int page, int limit, String sortRaw) {
		if (page < 1 || limit < 1 || limit > 100) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số phân trang không hợp lệ",
					Map.of("page", "page >= 1", "limit", "1–100"));
		}
		String orderBy;
		try {
			orderBy = SupplierJdbcRepository.resolveListOrderBy(sortRaw);
		}
		catch (IllegalArgumentException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số sort không hợp lệ",
					Map.of("sort", "Giá trị không nằm trong whitelist"));
		}
		String status = normalizeListStatus(statusRaw);
		String search = searchRaw != null && !searchRaw.isBlank() ? searchRaw.trim() : null;
		long total = supplierJdbcRepository.countList(search, status);
		int offset = (page - 1) * limit;
		List<SupplierListItemData> items = supplierJdbcRepository.findListPage(search, status, orderBy, limit,
				offset);
		return new SupplierListPageData(items, page, limit, total);
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
	public SupplierDetailData getById(int id) {
		return supplierJdbcRepository.findDetailById(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhà cung cấp"));
	}

	@Transactional(readOnly = true)
	public java.util.Optional<Integer> findIdBySupplierCode(String supplierCode) {
		if (!StringUtils.hasText(supplierCode)) {
			return java.util.Optional.empty();
		}
		return supplierJdbcRepository.findIdBySupplierCode(supplierCode.trim());
	}

	@Transactional
	public SupplierDetailData create(SupplierCreateRequest req) {
		String code = req.supplierCode().trim();
		String name = req.name().trim();
		String contact = req.contactPerson().trim();
		String phone = req.phone().trim();
		if (supplierJdbcRepository.existsSupplierCode(code)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Mã nhà cung cấp đã tồn tại",
					Map.of("supplierCode", "Trùng supplier_code"));
		}
		String email = normalizeEmailForStore(req.email());
		validateEmailFormat(email);
		String address = normalizeBlankToNull(req.address());
		String taxCode = normalizeTaxCode(req.taxCode());
		String status = normalizeSupplierStatus(req.status());
		int id = supplierJdbcRepository.insertSupplier(code, name, contact, phone, email, address, taxCode, status);
		return supplierJdbcRepository.findDetailById(id).orElseThrow(
				() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc lại nhà cung cấp sau tạo"));
	}

	@Transactional
	public SupplierDetailData patch(int id, JsonNode body) {
		if (body == null || !body.isObject() || body.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Body PATCH không được rỗng");
		}
		SupplierLockRow locked = supplierJdbcRepository.lockSupplierForUpdate(id).orElseThrow(
				() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhà cung cấp"));
		String newCode = locked.supplierCode();
		String newName = locked.name();
		String newContact = locked.contactPerson();
		String newPhone = locked.phone();
		String newEmail = locked.email();
		String newAddress = locked.address();
		String newTax = locked.taxCode();
		String newStatus = locked.status();
		boolean any = false;

		if (body.has("supplierCode")) {
			JsonNode n = body.get("supplierCode");
			if (!n.isNull()) {
				any = true;
				newCode = requireNonBlank(n.asText(), "supplierCode", 50);
				if (supplierJdbcRepository.existsOtherSupplierCode(id, newCode)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Mã nhà cung cấp đã tồn tại");
				}
			}
		}
		if (body.has("name")) {
			JsonNode n = body.get("name");
			if (!n.isNull()) {
				any = true;
				newName = requireNonBlank(n.asText(), "name", 255);
			}
		}
		if (body.has("contactPerson")) {
			JsonNode n = body.get("contactPerson");
			if (!n.isNull()) {
				any = true;
				newContact = requireNonBlank(n.asText(), "contactPerson", 255);
			}
		}
		if (body.has("phone")) {
			JsonNode n = body.get("phone");
			if (!n.isNull()) {
				any = true;
				newPhone = requireNonBlank(n.asText(), "phone", 20);
			}
		}
		if (body.has("email")) {
			JsonNode n = body.get("email");
			any = true;
			newEmail = n.isNull() ? null : normalizeEmailForStore(n.asText(""));
			validateEmailFormat(newEmail);
		}
		if (body.has("address")) {
			JsonNode n = body.get("address");
			any = true;
			newAddress = n.isNull() ? null : normalizeBlankToNull(n.asText(""));
		}
		if (body.has("taxCode")) {
			JsonNode n = body.get("taxCode");
			any = true;
			newTax = n.isNull() ? null : normalizeTaxCode(n.asText(""));
			if (newTax != null && newTax.length() > 50) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "taxCode không hợp lệ",
						Map.of("taxCode", "Tối đa 50"));
			}
		}
		if (body.has("status")) {
			JsonNode n = body.get("status");
			if (!n.isNull()) {
				any = true;
				newStatus = normalizeSupplierStatusRequired(n.asText());
			}
		}
		if (!any) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một trường hợp lệ để cập nhật");
		}
		supplierJdbcRepository.updateSupplier(id, newCode, newName, newContact, newPhone, newEmail, newAddress,
				newTax, newStatus);
		return supplierJdbcRepository.findDetailById(id).orElseThrow(
				() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhà cung cấp"));
	}

	@Transactional
	public SupplierDeleteData delete(int id, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt, "Chỉ tài khoản Owner mới được xóa nhà cung cấp");
		supplierJdbcRepository.lockSupplierForUpdate(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhà cung cấp"));
		assertDeletableOrThrow(id);
		int n = supplierJdbcRepository.deleteSupplier(id);
		if (n != 1) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Xóa nhà cung cấp không thành công");
		}
		return new SupplierDeleteData(id, true);
	}

	private void assertDeletableOrThrow(int supplierId) {
		if (supplierJdbcRepository.existsStockReceiptForSupplier(supplierId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể xóa nhà cung cấp đã có phiếu nhập kho",
					Map.of("reason", "HAS_RECEIPTS"));
		}
		if (supplierJdbcRepository.existsPartnerDebtForSupplier(supplierId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể xóa nhà cung cấp đang có công nợ",
					Map.of("reason", "HAS_PARTNER_DEBTS"));
		}
	}

	@Transactional
	public SupplierBulkDeleteData bulkDelete(SuppliersBulkDeleteRequest req, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt, "Chỉ tài khoản Owner mới được xóa nhà cung cấp");
		List<Integer> ids = req.ids();
		Set<Integer> uniq = new HashSet<>(ids);
		if (uniq.size() != ids.size()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách ids không được trùng lặp");
		}
		for (int sid : ids) {
			if (!supplierJdbcRepository.existsSupplierId(sid)) {
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không thể xóa toàn bộ: ít nhất một nhà cung cấp không tồn tại",
						Map.of("failedId", String.valueOf(sid), "reason", "NOT_FOUND"));
			}
		}
		for (int sid : ids) {
			if (supplierJdbcRepository.existsStockReceiptForSupplier(sid)) {
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không thể xóa toàn bộ: ít nhất một nhà cung cấp không đủ điều kiện",
						Map.of("failedId", String.valueOf(sid), "reason", "HAS_RECEIPTS"));
			}
		}
		for (int sid : ids) {
			if (supplierJdbcRepository.existsPartnerDebtForSupplier(sid)) {
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không thể xóa toàn bộ: ít nhất một nhà cung cấp không đủ điều kiện",
						Map.of("failedId", String.valueOf(sid), "reason", "HAS_PARTNER_DEBTS"));
			}
		}
		supplierJdbcRepository.lockSuppliersForUpdate(ids);
		int deleted = supplierJdbcRepository.deleteSuppliers(ids);
		if (deleted != ids.size()) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Xóa bulk không khớp số dòng");
		}
		return new SupplierBulkDeleteData(new ArrayList<>(ids), deleted);
	}

	private static String requireNonBlank(String raw, String field, int maxLen) {
		String t = raw == null ? "" : raw.trim();
		if (t.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường không được để trống", Map.of(field, "Bắt buộc"));
		}
		if (t.length() > maxLen) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường quá dài", Map.of(field, "Tối đa " + maxLen));
		}
		return t;
	}

	private static String normalizeSupplierStatus(String raw) {
		if (!StringUtils.hasText(raw)) {
			return "Active";
		}
		return normalizeSupplierStatusRequired(raw);
	}

	private static String normalizeSupplierStatusRequired(String raw) {
		String s = raw.trim();
		if ("Active".equals(s) || "Inactive".equals(s)) {
			return s;
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "status không hợp lệ");
	}

	private static String normalizeBlankToNull(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		return raw.trim();
	}

	private static String normalizeEmailForStore(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		return raw.trim();
	}

	private static String normalizeTaxCode(String raw) {
		if (raw == null) {
			return null;
		}
		String t = raw.trim();
		return t.isEmpty() ? null : t;
	}

	private static void validateEmailFormat(String email) {
		if (email == null) {
			return;
		}
		if (!EMAIL_PATTERN.matcher(email).matches()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "email không hợp lệ", Map.of("email", "Định dạng email không đúng"));
		}
	}

}
