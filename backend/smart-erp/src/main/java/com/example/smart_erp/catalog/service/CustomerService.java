package com.example.smart_erp.catalog.service;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.fasterxml.jackson.databind.JsonNode;

import com.example.smart_erp.catalog.dto.CustomerCreateRequest;
import com.example.smart_erp.catalog.dto.CustomersBulkDeleteRequest;
import com.example.smart_erp.catalog.repository.CustomerJdbcRepository;
import com.example.smart_erp.catalog.repository.CustomerJdbcRepository.CustomerLockRow;
import com.example.smart_erp.catalog.response.CustomerBulkDeleteData;
import com.example.smart_erp.catalog.response.CustomerData;
import com.example.smart_erp.catalog.response.CustomerDeleteData;
import com.example.smart_erp.catalog.response.CustomerListPageData;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.dispatch.StockDispatchAccessPolicy;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;

import org.springframework.security.oauth2.jwt.Jwt;

@Service
public class CustomerService {

	private static final Pattern EMAIL_PATTERN = Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");

	private final CustomerJdbcRepository customerJdbcRepository;

	public CustomerService(CustomerJdbcRepository customerJdbcRepository) {
		this.customerJdbcRepository = customerJdbcRepository;
	}

	@Transactional(readOnly = true)
	public CustomerListPageData list(String searchRaw, String statusRaw, int page, int limit, String sortRaw) {
		if (page < 1 || limit < 1 || limit > 100) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số phân trang không hợp lệ",
					Map.of("page", "page >= 1", "limit", "1–100"));
		}
		String orderBy;
		try {
			orderBy = CustomerJdbcRepository.resolveListOrderBy(sortRaw);
		}
		catch (IllegalArgumentException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số sort không hợp lệ",
					Map.of("sort", "Giá trị không nằm trong whitelist"));
		}
		String status = normalizeListStatus(statusRaw);
		String search = searchRaw != null && !searchRaw.isBlank() ? searchRaw.trim() : null;
		long total = customerJdbcRepository.countList(search, status);
		int offset = (page - 1) * limit;
		List<CustomerData> items = customerJdbcRepository.findListPage(search, status, orderBy, limit, offset);
		return new CustomerListPageData(items, page, limit, total);
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
	public CustomerData getById(int id) {
		return customerJdbcRepository.findDetailById(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy khách hàng"));
	}

	@Transactional(readOnly = true)
	public java.util.Optional<Integer> findIdByCustomerCode(String customerCode) {
		if (!StringUtils.hasText(customerCode)) {
			return java.util.Optional.empty();
		}
		return customerJdbcRepository.findIdByCustomerCode(customerCode.trim());
	}

	@Transactional
	public CustomerData create(CustomerCreateRequest req) {
		String code = req.customerCode().trim();
		String name = req.name().trim();
		String phone = req.phone().trim();
		if (customerJdbcRepository.existsCustomerCode(code)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Mã khách hàng đã tồn tại",
					Map.of("field", "customerCode"));
		}
		String email = normalizeEmailForStore(req.email());
		validateEmailFormat(email);
		String address = normalizeBlankToNull(req.address());
		String status = normalizeCustomerStatus(req.status());
		int id = customerJdbcRepository.insertCustomer(code, name, phone, email, address, status);
		return customerJdbcRepository.findDetailById(id).orElseThrow(
				() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc lại khách hàng sau tạo"));
	}

	@Transactional
	public CustomerData patch(int id, JsonNode body) {
		return patch(id, body, null);
	}

	@Transactional
	public CustomerData patch(int id, JsonNode body, Jwt jwt) {
		if (body == null || !body.isObject() || body.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Body PATCH không được rỗng");
		}
		if (body.has("loyaltyPoints") && jwt != null && isStaffRole(jwt)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền chỉnh điểm tích lũy");
		}
		CustomerLockRow locked = customerJdbcRepository.lockCustomerForUpdate(id).orElseThrow(
				() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy khách hàng"));
		String newCode = locked.customerCode();
		String newName = locked.name();
		String newPhone = locked.phone();
		String newEmail = locked.email();
		String newAddress = locked.address();
		int newLoyalty = locked.loyaltyPoints();
		String newStatus = locked.status();
		boolean any = false;

		if (body.has("customerCode")) {
			JsonNode n = body.get("customerCode");
			if (!n.isNull()) {
				any = true;
				newCode = requireNonBlank(n.asText(), "customerCode", 50);
				if (customerJdbcRepository.existsOtherCustomerCode(id, newCode)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Mã khách hàng đã tồn tại",
							Map.of("field", "customerCode"));
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
		if (body.has("loyaltyPoints")) {
			JsonNode n = body.get("loyaltyPoints");
			if (!n.isNull()) {
				any = true;
				if (!n.isIntegralNumber()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "loyaltyPoints không hợp lệ");
				}
				int lp = n.intValue();
				if (lp < 0) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "loyaltyPoints không hợp lệ");
				}
				newLoyalty = lp;
			}
		}
		if (body.has("status")) {
			JsonNode n = body.get("status");
			if (!n.isNull()) {
				any = true;
				newStatus = normalizeCustomerStatusRequired(n.asText());
			}
		}
		if (!any) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một trường hợp lệ để cập nhật");
		}
		customerJdbcRepository.updateCustomer(id, newCode, newName, newPhone, newEmail, newAddress, newLoyalty,
				newStatus);
		return customerJdbcRepository.findDetailById(id).orElseThrow(
				() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy khách hàng"));
	}

	@Transactional
	public CustomerDeleteData delete(int id, Jwt jwt) {
		assertAdminOnlyForCustomerDelete(jwt);
		customerJdbcRepository.lockCustomerForUpdate(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy khách hàng"));
		assertSingleCustomerSoftDeletableOrThrow(id);
		int n = customerJdbcRepository.softDeleteCustomer(id);
		if (n != 1) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Xóa khách hàng không thành công");
		}
		return new CustomerDeleteData(id, true);
	}

	private static void assertAdminOnlyForCustomerDelete(Jwt jwt) {
		if (!StockDispatchAccessPolicy.isAdmin(jwt)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền thực hiện thao tác này.");
		}
	}

	/** Task052 soft-delete: only non-terminal orders block. */
	private void assertSingleCustomerSoftDeletableOrThrow(int customerId) {
		if (customerJdbcRepository.existsOpenSalesOrderForCustomer(customerId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể xóa khách hàng vì còn đơn hàng chưa hoàn tất.",
					Map.of("reason", "HAS_OPEN_SALES_ORDERS"));
		}
		if (customerJdbcRepository.existsPartnerDebtForCustomer(customerId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể xóa khách hàng đang có công nợ",
					Map.of("reason", "HAS_PARTNER_DEBTS"));
		}
	}

	/** Task053 bulk hard-delete: any sales order blocks. */
	private void assertBulkCustomerDeletableOrThrow(int customerId) {
		if (customerJdbcRepository.existsSalesOrderForCustomer(customerId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể xóa toàn bộ: ít nhất một khách hàng không đủ điều kiện",
					Map.of("failedId", String.valueOf(customerId), "reason", "HAS_SALES_ORDERS"));
		}
		if (customerJdbcRepository.existsPartnerDebtForCustomer(customerId)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể xóa toàn bộ: ít nhất một khách hàng không đủ điều kiện",
					Map.of("failedId", String.valueOf(customerId), "reason", "HAS_PARTNER_DEBTS"));
		}
	}

	@Transactional
	public CustomerBulkDeleteData bulkDelete(CustomersBulkDeleteRequest req, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt, "Chỉ chủ cửa hàng mới được xóa khách hàng");
		List<Integer> ids = dedupePreserveOrder(req.ids());
		if (ids.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách id không hợp lệ",
					Map.of("ids", "Cần từ 1 đến 50 id khác nhau (trùng trong mảng sẽ được gộp)"));
		}
		if (ids.size() > 50) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách id không hợp lệ",
					Map.of("ids", "Cần từ 1 đến 50 id khác nhau (trùng trong mảng sẽ được gộp)"));
		}
		for (int cid : ids) {
			if (!customerJdbcRepository.existsCustomerId(cid)) {
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không thể xóa toàn bộ: ít nhất một khách hàng không đủ điều kiện",
						Map.of("failedId", String.valueOf(cid), "reason", "NOT_FOUND"));
			}
		}
		for (int cid : ids) {
			assertBulkCustomerDeletableOrThrow(cid);
		}
		customerJdbcRepository.lockCustomersForUpdate(ids);
		int deleted = customerJdbcRepository.deleteCustomersHard(ids);
		if (deleted != ids.size()) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Xóa bulk không khớp số dòng");
		}
		return new CustomerBulkDeleteData(new ArrayList<>(ids), deleted);
	}

	private static List<Integer> dedupePreserveOrder(List<Integer> raw) {
		Set<Integer> seen = new LinkedHashSet<>();
		List<Integer> out = new ArrayList<>();
		for (Integer id : raw) {
			if (id == null || id <= 0) {
				continue;
			}
			if (seen.add(id)) {
				out.add(id);
			}
		}
		return out;
	}

	private static boolean isStaffRole(Jwt jwt) {
		String role = jwt.getClaimAsString("role");
		return StringUtils.hasText(role) && "Staff".equalsIgnoreCase(role.trim());
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

	private static String normalizeCustomerStatus(String raw) {
		if (!StringUtils.hasText(raw)) {
			return "Active";
		}
		return normalizeCustomerStatusRequired(raw);
	}

	private static String normalizeCustomerStatusRequired(String raw) {
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

	private static void validateEmailFormat(String email) {
		if (email == null) {
			return;
		}
		if (!EMAIL_PATTERN.matcher(email).matches()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "email không hợp lệ", Map.of("email", "Định dạng email không đúng"));
		}
	}
}
