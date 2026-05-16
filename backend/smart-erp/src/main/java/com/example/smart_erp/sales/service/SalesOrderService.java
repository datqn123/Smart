package com.example.smart_erp.sales.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.DateTimeException;
import java.time.LocalDate;
import java.time.Year;
import java.time.ZoneId;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.fasterxml.jackson.databind.JsonNode;

import com.example.smart_erp.catalog.repository.CustomerJdbcRepository;
import com.example.smart_erp.catalog.repository.ProductJdbcRepository;
import com.example.smart_erp.catalog.response.ProductUnitRow;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.finance.ledger.BusinessFinanceLedgerPostingService;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.example.smart_erp.sales.SalesOrderAccessPolicy;
import com.example.smart_erp.sales.dto.RetailCheckoutRequest;
import com.example.smart_erp.sales.dto.RetailVoucherPreviewRequest;
import com.example.smart_erp.sales.dto.SalesOrderCreateRequest;
import com.example.smart_erp.sales.dto.SalesOrderLineRequest;
import com.example.smart_erp.sales.repository.PosProductJdbcRepository;
import com.example.smart_erp.sales.repository.SalesOrderJdbcRepository;
import com.example.smart_erp.sales.repository.SalesOrderJdbcRepository.OrderLockRow;
import com.example.smart_erp.sales.repository.VoucherJdbcRepository;
import com.example.smart_erp.sales.repository.VoucherJdbcRepository.VoucherRow;
import com.example.smart_erp.sales.stock.RetailStockService;
import com.example.smart_erp.sales.response.PosProductSearchData;
import com.example.smart_erp.sales.response.RetailVoucherPreviewData;
import com.example.smart_erp.sales.response.SalesOrderCancelData;
import com.example.smart_erp.sales.response.SalesOrderDetailData;
import com.example.smart_erp.sales.response.SalesOrderListPageData;

import org.springframework.security.oauth2.jwt.Jwt;

@Service
public class SalesOrderService {

	private static final ZoneId RETAIL_HISTORY_ZONE = ZoneId.of("Asia/Ho_Chi_Minh");

	private static final BigDecimal PRICE_TOLERANCE = new BigDecimal("0.10");

	private final SalesOrderJdbcRepository salesOrderJdbcRepository;

	private final VoucherJdbcRepository voucherJdbcRepository;

	private final CustomerJdbcRepository customerJdbcRepository;

	private final ProductJdbcRepository productJdbcRepository;

	private final PosProductJdbcRepository posProductJdbcRepository;

	private final RetailStockService retailStockService;

	private final BusinessFinanceLedgerPostingService financeLedgerPostingService;

	public SalesOrderService(SalesOrderJdbcRepository salesOrderJdbcRepository,
			VoucherJdbcRepository voucherJdbcRepository, CustomerJdbcRepository customerJdbcRepository,
			ProductJdbcRepository productJdbcRepository, PosProductJdbcRepository posProductJdbcRepository,
			RetailStockService retailStockService, BusinessFinanceLedgerPostingService financeLedgerPostingService) {
		this.salesOrderJdbcRepository = salesOrderJdbcRepository;
		this.voucherJdbcRepository = voucherJdbcRepository;
		this.customerJdbcRepository = customerJdbcRepository;
		this.productJdbcRepository = productJdbcRepository;
		this.posProductJdbcRepository = posProductJdbcRepository;
		this.retailStockService = retailStockService;
		this.financeLedgerPostingService = financeLedgerPostingService;
	}

	@Transactional(readOnly = true)
	public SalesOrderListPageData list(Jwt jwt, String orderChannelRaw, String searchRaw, String statusRaw, int page,
			int limit, String sortRaw, String paymentStatusRaw) {
		if (page < 1 || limit < 1 || limit > 100) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số phân trang không hợp lệ",
					Map.of("page", "page >= 1", "limit", "1–100"));
		}
		String orderChannel = orderChannelRaw != null && !orderChannelRaw.isBlank() ? orderChannelRaw.trim() : null;
		SalesOrderAccessPolicy.assertCanListWithoutOrderChannelFilter(jwt, orderChannel);
		String orderBy;
		try {
			orderBy = SalesOrderJdbcRepository.resolveListOrderBy(sortRaw);
		}
		catch (IllegalArgumentException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số sort không hợp lệ",
					Map.of("sort", "Giá trị không nằm trong whitelist"));
		}
		String status = normalizeListStatus(statusRaw);
		String paymentStatus = normalizePaymentStatusFilter(paymentStatusRaw);
		String search = searchRaw != null && !searchRaw.isBlank() ? searchRaw.trim() : null;
		long total = salesOrderJdbcRepository.countList(orderChannel, search, status, paymentStatus);
		int offset = (page - 1) * limit;
		var items = salesOrderJdbcRepository.findListPage(orderChannel, search, status, paymentStatus, orderBy, limit,
				offset);
		return new SalesOrderListPageData(items, page, limit, total);
	}

	/**
	 * Task102 — lịch sử hóa đơn bán lẻ (Retail, Delivered/Cancelled), có lọc ngày theo
	 * {@value #RETAIL_HISTORY_ZONE}.
	 */
	@Transactional(readOnly = true)
	public SalesOrderListPageData listRetailHistory(String searchRaw, String dateFromRaw, String dateToRaw, int page,
			int limit, String sortRaw) {
		if (page < 1 || limit < 1 || limit > 100) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số phân trang không hợp lệ",
					Map.of("page", "page >= 1", "limit", "1–100"));
		}
		String orderBy;
		try {
			orderBy = SalesOrderJdbcRepository.resolveRetailHistoryOrderBy(sortRaw);
		}
		catch (IllegalArgumentException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số sort không hợp lệ",
					Map.of("sort", "Giá trị không nằm trong whitelist"));
		}
		String search = normalizeRetailHistorySearch(searchRaw);
		LocalDate dateFrom = parseIsoDateOrNull(dateFromRaw, "dateFrom");
		LocalDate dateTo = parseIsoDateOrNull(dateToRaw, "dateTo");
		if (dateFrom != null && dateTo != null && dateFrom.isAfter(dateTo)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of("dateTo", "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu"));
		}
		Instant createdFrom = dateFrom == null ? null : dateFrom.atStartOfDay(RETAIL_HISTORY_ZONE).toInstant();
		Instant createdToExclusive = dateTo == null ? null : dateTo.plusDays(1).atStartOfDay(RETAIL_HISTORY_ZONE).toInstant();
		long total = salesOrderJdbcRepository.countRetailHistory(search, createdFrom, createdToExclusive);
		int offset = (page - 1) * limit;
		var items = salesOrderJdbcRepository.findRetailHistoryPage(search, createdFrom, createdToExclusive, orderBy,
				limit, offset);
		return new SalesOrderListPageData(items, page, limit, total);
	}

	private static String normalizeRetailHistorySearch(String searchRaw) {
		if (searchRaw == null || searchRaw.isBlank()) {
			return null;
		}
		String t = searchRaw.trim();
		if (t.length() > 100) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of("search", "Tối đa 100 ký tự"));
		}
		return t;
	}

	private static LocalDate parseIsoDateOrNull(String raw, String fieldName) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		try {
			return LocalDate.parse(raw.trim());
		}
		catch (DateTimeException e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of(fieldName, "Định dạng ngày phải là yyyy-MM-dd"));
		}
	}

	private static String normalizeListStatus(String statusRaw) {
		if (statusRaw == null || statusRaw.isBlank()) {
			return "all";
		}
		String s = statusRaw.trim();
		if ("all".equalsIgnoreCase(s)) {
			return "all";
		}
		if ("Pending".equals(s) || "Processing".equals(s) || "Partial".equals(s) || "Shipped".equals(s)
				|| "Delivered".equals(s) || "Cancelled".equals(s)) {
			return s;
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số status không hợp lệ");
	}

	private static String normalizePaymentStatusFilter(String raw) {
		if (raw == null || raw.isBlank()) {
			return "all";
		}
		String s = raw.trim();
		if ("all".equalsIgnoreCase(s)) {
			return "all";
		}
		if ("Paid".equals(s) || "Unpaid".equals(s) || "Partial".equals(s)) {
			return s;
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số paymentStatus không hợp lệ");
	}

	@Transactional(readOnly = true)
	public SalesOrderDetailData getById(int id) {
		return salesOrderJdbcRepository.findDetailById(id)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đơn hàng"));
	}

	@Transactional
	public SalesOrderDetailData create(SalesOrderCreateRequest body, Jwt jwt) {
		String ch = body.orderChannel();
		if (!"Wholesale".equals(ch) && !"Return".equals(ch)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "orderChannel chỉ được Wholesale hoặc Return");
		}
		if (!customerJdbcRepository.existsCustomerId(body.customerId())) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy khách hàng");
		}
		if ("Return".equals(ch) && body.refSalesOrderId() != null) {
			Optional<Integer> refCust = salesOrderJdbcRepository.findCustomerIdOfOrder(body.refSalesOrderId());
			if (refCust.isEmpty()) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Đơn tham chiếu không tồn tại");
			}
			if (!refCust.get().equals(body.customerId())) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Đơn trả phải cùng khách hàng với đơn gốc");
			}
		}
		validateLines(body.lines());
		BigDecimal subtotal = computeSubtotal(body.lines());
		BigDecimal discount = body.discountAmount() != null ? body.discountAmount() : BigDecimal.ZERO;
		if (discount.signum() < 0 || discount.compareTo(subtotal) > 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "discountAmount không hợp lệ");
		}
		String payment = body.paymentStatus() != null && !body.paymentStatus().isBlank() ? body.paymentStatus()
				: "Unpaid";
		assertPaymentStatus(payment);
		String status = body.status() != null && !body.status().isBlank() ? body.status() : "Pending";
		assertHeaderStatus(status);
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		String tempCode = "TMP-" + UUID.randomUUID().toString().replace("-", "");
		int id = salesOrderJdbcRepository.insertOrderHeader(tempCode, body.customerId(), uid, subtotal, discount,
				status, ch, payment, body.shippingAddress(), body.notes(), null, body.refSalesOrderId(), null, null);
		if (id <= 0) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không tạo được đơn hàng");
		}
		salesOrderJdbcRepository.updateOrderCode(id, buildOrderCode(id));
		for (SalesOrderLineRequest line : body.lines()) {
			salesOrderJdbcRepository.insertOrderLine(id, line.productId(), line.unitId(), line.quantity(),
					line.unitPrice());
		}
		salesOrderJdbcRepository.loadOrderFinancialForLedger(id)
				.ifPresent(fin -> financeLedgerPostingService.tryPostOrderLedgerOnFinancialState(fin, uid));
		return getById(id);
	}

	@Transactional
	public SalesOrderDetailData retailCheckout(RetailCheckoutRequest body, Jwt jwt) {
		if (Boolean.FALSE.equals(body.walkIn()) && (body.customerId() == null || body.customerId() <= 0)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần customerId hoặc walkIn = true");
		}
		int customerId;
		if (body.customerId() != null && body.customerId() > 0) {
			if (!customerJdbcRepository.existsCustomerId(body.customerId())) {
				throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy khách hàng");
			}
			customerId = body.customerId();
		}
		else {
			customerId = salesOrderJdbcRepository.findWalkinCustomerId()
					.orElseThrow(() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR,
							"Chưa cấu hình khách WALKIN trên hệ thống"));
		}
		validateLines(body.lines());
		BigDecimal subtotal = computeSubtotal(body.lines());
		BigDecimal manualDiscount = body.discountAmount() != null ? body.discountAmount() : BigDecimal.ZERO;
		if (manualDiscount.signum() < 0 || manualDiscount.compareTo(subtotal) > 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "discountAmount không hợp lệ");
		}
		Integer voucherId = null;
		BigDecimal voucherDiscount = BigDecimal.ZERO;
		if (StringUtils.hasText(body.voucherCode())) {
			String trimmed = body.voucherCode().trim();
			VoucherRow v = voucherJdbcRepository.lockVoucherByCodeForUpdate(trimmed)
					.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Mã giảm giá không hợp lệ"));
			assertRetailVoucherApplicableForCheckout(v);
			voucherId = v.id();
			voucherDiscount = computeVoucherDiscount(subtotal, v);
		}
		BigDecimal totalDiscount = manualDiscount.add(voucherDiscount);
		if (totalDiscount.compareTo(subtotal) > 0) {
			totalDiscount = subtotal;
		}
		String payment = body.paymentStatus() != null && !body.paymentStatus().isBlank() ? body.paymentStatus()
				: "Paid";
		assertPaymentStatus(payment);
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		String shiftRef = body.shiftReference() != null && body.shiftReference().length() > 100
				? body.shiftReference().substring(0, 100)
				: body.shiftReference();
		String tempCode = "TMP-" + UUID.randomUUID().toString().replace("-", "");
		int id = salesOrderJdbcRepository.insertOrderHeader(tempCode, customerId, uid, subtotal, totalDiscount,
				"Delivered", "Retail", payment, null, body.notes(), null, null, voucherId, shiftRef);
		if (id <= 0) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không tạo được đơn hàng");
		}
		salesOrderJdbcRepository.updateOrderCode(id, buildOrderCode(id));
		for (SalesOrderLineRequest line : body.lines()) {
			salesOrderJdbcRepository.insertOrderLine(id, line.productId(), line.unitId(), line.quantity(),
					line.unitPrice());
		}
		String orderCode = salesOrderJdbcRepository.findOrderCode(id).orElseGet(() -> buildOrderCode(id));
		retailStockService.deductStockForRetailCheckout(id, orderCode, uid, body.lines());
		if (voucherId != null) {
			voucherJdbcRepository.incrementUsedCount(voucherId);
			voucherJdbcRepository.insertRedemption(voucherId, id);
		}
		salesOrderJdbcRepository.loadOrderFinancialForLedger(id)
				.ifPresent(fin -> financeLedgerPostingService.postRetailSalesRevenueIfAbsent(fin, uid));
		return getById(id);
	}

	@Transactional(readOnly = true)
	public RetailVoucherPreviewData retailVoucherPreview(RetailVoucherPreviewRequest body, Jwt jwt) {
		StockReceiptAccessPolicy.parseUserId(jwt);
		boolean hasId = body.voucherId() != null && body.voucherId() > 0;
		boolean hasCode = StringUtils.hasText(body.voucherCode());
		if (!hasId && !hasCode) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần voucherId hoặc voucherCode");
		}
		VoucherRow v;
		if (hasId) {
			v = voucherJdbcRepository.findVoucherById(body.voucherId())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Không tìm thấy mã giảm giá"));
			if (hasCode && !v.code().equalsIgnoreCase(body.voucherCode().trim())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "voucherId và voucherCode không khớp");
			}
		}
		else {
			v = voucherJdbcRepository.findVoucherByCodeIgnoreCase(body.voucherCode().trim())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "Không tìm thấy mã giảm giá"));
		}
		if (!isActiveInWindow(v)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Mã giảm giá không hợp lệ hoặc đã hết hạn");
		}
		if (!hasRemainingUses(v)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Mã giảm giá đã hết lượt sử dụng");
		}
		validateLines(body.lines());
		BigDecimal subtotal = computeSubtotal(body.lines());
		BigDecimal manualDiscount = body.discountAmount() != null ? body.discountAmount() : BigDecimal.ZERO;
		if (manualDiscount.signum() < 0 || manualDiscount.compareTo(subtotal) > 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "discountAmount không hợp lệ");
		}
		BigDecimal voucherDiscount = computeVoucherDiscount(subtotal, v);
		BigDecimal totalDiscount = manualDiscount.add(voucherDiscount);
		if (totalDiscount.compareTo(subtotal) > 0) {
			totalDiscount = subtotal;
			voucherDiscount = subtotal.subtract(manualDiscount).max(BigDecimal.ZERO);
		}
		BigDecimal payable = subtotal.subtract(totalDiscount).max(BigDecimal.ZERO);
		return new RetailVoucherPreviewData(true, null, v.id(), v.code(), v.name(), v.discountType(), v.discountValue(),
				subtotal, manualDiscount, voucherDiscount, totalDiscount, payable);
	}

	private static void assertRetailVoucherApplicableForCheckout(VoucherRow v) {
		if (!isActiveInWindow(v)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Mã giảm giá không hợp lệ hoặc đã hết hạn");
		}
		if (!hasRemainingUses(v)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Mã giảm giá đã hết lượt sử dụng");
		}
	}

	private static boolean isActiveInWindow(VoucherRow v) {
		LocalDate today = LocalDate.now();
		if (!v.isActive()) {
			return false;
		}
		if (v.validFrom() != null && today.isBefore(v.validFrom())) {
			return false;
		}
		if (v.validTo() != null && today.isAfter(v.validTo())) {
			return false;
		}
		return true;
	}

	private static boolean hasRemainingUses(VoucherRow v) {
		return v.maxUses() == null || v.usedCount() < v.maxUses();
	}

	private static BigDecimal computeVoucherDiscount(BigDecimal subtotal, VoucherRow v) {
		if ("Percent".equalsIgnoreCase(v.discountType())) {
			return subtotal.multiply(v.discountValue()).divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
		}
		if ("FixedAmount".equalsIgnoreCase(v.discountType())) {
			return v.discountValue().min(subtotal).max(BigDecimal.ZERO);
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Loại voucher không hỗ trợ");
	}

	@Transactional
	public SalesOrderDetailData patch(int id, JsonNode body, Jwt jwt) {
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		if (body == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Body không được rỗng");
		}
		Optional<OrderLockRow> locked = salesOrderJdbcRepository.lockOrderForUpdate(id);
		if (locked.isEmpty()) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đơn hàng");
		}
		OrderLockRow row = locked.get();
		if ("Cancelled".equals(row.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể sửa đơn đã hủy");
		}
		String newStatus = readStringEnum(body, "status");
		String newPayment = readStringEnum(body, "paymentStatus");
		boolean inclShip = body != null && body.has("shippingAddress");
		String shipVal = null;
		if (inclShip) {
			JsonNode n = body.get("shippingAddress");
			if (n.isNull()) {
				shipVal = null;
			}
			else if (n.isTextual()) {
				shipVal = n.asText();
			}
			else {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường shippingAddress không hợp lệ");
			}
		}
		boolean inclNotes = body != null && body.has("notes");
		String notesVal = null;
		if (inclNotes) {
			JsonNode n = body.get("notes");
			if (n.isNull()) {
				notesVal = null;
			}
			else if (n.isTextual()) {
				notesVal = n.asText();
			}
			else {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường notes không hợp lệ");
			}
		}
		BigDecimal newDiscount = readBigDecimal(body, "discountAmount");
		if (newStatus != null) {
			assertHeaderStatus(newStatus);
		}
		if (newPayment != null) {
			assertPaymentStatus(newPayment);
		}
		if (newDiscount != null) {
			if (newDiscount.signum() < 0 || newDiscount.compareTo(row.totalAmount()) > 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "discountAmount không hợp lệ");
			}
		}
		if (newStatus == null && newPayment == null && !inclShip && !inclNotes && newDiscount == null) {
			return getById(id);
		}
		String priorPayment = row.paymentStatus() != null ? row.paymentStatus() : "Unpaid";
		String priorStatus = row.status();
		salesOrderJdbcRepository.patchOrder(id, newStatus, newPayment, inclShip, shipVal, inclNotes, notesVal,
				newDiscount);
		boolean paymentBecamePaid = newPayment != null && "Paid".equals(newPayment)
				&& !"Paid".equalsIgnoreCase(priorPayment);
		boolean statusBecameDelivered = newStatus != null && "Delivered".equals(newStatus)
				&& !"Delivered".equalsIgnoreCase(priorStatus);
		if (paymentBecamePaid || statusBecameDelivered) {
			salesOrderJdbcRepository.loadOrderFinancialForLedger(id)
					.ifPresent(fin -> financeLedgerPostingService.tryPostOrderLedgerOnFinancialState(fin, uid));
		}
		return getById(id);
	}

	private static String readStringEnum(JsonNode root, String field) {
		if (root == null || !root.has(field) || root.get(field).isNull()) {
			return null;
		}
		JsonNode n = root.get(field);
		if (!n.isTextual()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường " + field + " không hợp lệ");
		}
		return n.asText();
	}

	private static BigDecimal readBigDecimal(JsonNode root, String field) {
		if (root == null || !root.has(field) || root.get(field).isNull()) {
			return null;
		}
		JsonNode n = root.get(field);
		if (!n.isNumber()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trường " + field + " không hợp lệ");
		}
		return n.decimalValue();
	}

	@Transactional
	public SalesOrderCancelData cancel(int id, Jwt jwt) {
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		Optional<OrderLockRow> locked = salesOrderJdbcRepository.lockOrderForUpdate(id);
		if (locked.isEmpty()) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đơn hàng");
		}
		OrderLockRow row = locked.get();
		if ("Cancelled".equals(row.status())) {
			return new SalesOrderCancelData(id, "Cancelled", row.cancelledAt(), row.cancelledBy());
		}
		boolean hasDispatch = salesOrderJdbcRepository.countStockDispatchesForOrder(id) > 0
				|| salesOrderJdbcRepository.existsDispatchedLines(id);
		if (hasDispatch) {
			if ("Retail".equalsIgnoreCase(row.orderChannel())) {
				retailStockService.reverseDeductionForRetailCancel(id, uid);
			}
			else {
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Không thể hủy đơn — đã có phiếu xuất hoặc đã giao từ kho");
			}
		}
		if ("Retail".equalsIgnoreCase(row.orderChannel()) && row.voucherId() != null) {
			voucherJdbcRepository.reverseRedemptionForOrder(id);
		}
		if ("Retail".equalsIgnoreCase(row.orderChannel())) {
			salesOrderJdbcRepository.loadOrderFinancialForLedger(id)
					.ifPresent(fin -> financeLedgerPostingService.postRetailRefundIfAbsent(fin, uid));
		}
		salesOrderJdbcRepository.cancelOrder(id, uid);
		SalesOrderDetailData d = getById(id);
		return new SalesOrderCancelData(id, d.status(), d.cancelledAt(), d.cancelledBy());
	}

	@Transactional(readOnly = true)
	public PosProductSearchData searchPosProducts(String search, Integer categoryId, Integer locationId, int limit) {
		int lim = limit <= 0 ? 40 : Math.min(limit, 100);
		Integer effectiveLoc = locationId;
		if (effectiveLoc == null) {
			effectiveLoc = retailStockService.requireDefaultRetailLocationId();
		}
		return new PosProductSearchData(posProductJdbcRepository.search(search, categoryId, effectiveLoc, lim));
	}

	private void validateLines(List<SalesOrderLineRequest> lines) {
		if (lines == null || lines.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh sách dòng hàng không được rỗng");
		}
		for (SalesOrderLineRequest line : lines) {
			if (line.quantity() == null || line.quantity() <= 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Số lượng dòng không hợp lệ");
			}
			if (line.unitPrice() == null || line.unitPrice().signum() < 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Đơn giá không hợp lệ");
			}
			if (!salesOrderJdbcRepository.existsProductUnitForProduct(line.productId(), line.unitId())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Đơn vị không thuộc sản phẩm");
			}
			if (!productJdbcRepository.existsProductId(line.productId())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Sản phẩm không tồn tại");
			}
			validateUnitPriceAgainstCatalog(line.productId(), line.unitId(), line.unitPrice());
		}
	}

	private void validateUnitPriceAgainstCatalog(int productId, int unitId, BigDecimal unitPrice) {
		List<ProductUnitRow> units = productJdbcRepository.listUnitsWithCurrentPrices(productId);
		BigDecimal ref = units.stream().filter(u -> u.id() == unitId).map(ProductUnitRow::currentSalePrice)
				.findFirst().orElse(null);
		if (ref == null || ref.signum() <= 0) {
			return;
		}
		BigDecimal diff = unitPrice.subtract(ref).abs();
		BigDecimal ratio = diff.divide(ref, 4, RoundingMode.HALF_UP);
		if (ratio.compareTo(PRICE_TOLERANCE) > 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Đơn giá lệch quá mức cho phép so với giá niêm yết");
		}
	}

	private static BigDecimal computeSubtotal(List<SalesOrderLineRequest> lines) {
		BigDecimal sum = BigDecimal.ZERO;
		for (SalesOrderLineRequest line : lines) {
			sum = sum.add(line.unitPrice().multiply(BigDecimal.valueOf(line.quantity())));
		}
		return sum;
	}

	private static void assertPaymentStatus(String s) {
		if (!"Paid".equals(s) && !"Unpaid".equals(s) && !"Partial".equals(s)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "paymentStatus không hợp lệ");
		}
	}

	private static void assertHeaderStatus(String s) {
		if ("Cancelled".equals(s)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Không được đặt status Cancelled qua PATCH");
		}
		if (!"Pending".equals(s) && !"Processing".equals(s) && !"Partial".equals(s) && !"Shipped".equals(s)
				&& !"Delivered".equals(s)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "status không hợp lệ");
		}
	}

	private static String buildOrderCode(int id) {
		int year = Year.now(ZoneId.of("Asia/Ho_Chi_Minh")).getValue();
		return "SO-" + year + "-" + String.format("%06d", id);
	}
}
