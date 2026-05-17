package com.example.smart_erp.inventory.receipts.lifecycle;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import com.example.smart_erp.auth.repository.SystemLogJdbcRepository;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.finance.ledger.BusinessFinanceLedgerPostingService;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptLifecycleJdbcRepository.ReceiptHeaderLockRow;
import com.example.smart_erp.inventory.receipts.response.StockReceiptViewData;

@Service
public class StockReceiptLifecycleService {

	private static final int RECEIPT_CODE_RETRY = 5;

	private static final int REJECT_REASON_MIN_LEN = 15;

	private final StockReceiptLifecycleJdbcRepository repo;

	private final SystemLogJdbcRepository systemLogJdbcRepository;

	private final ObjectMapper objectMapper;

	private final StockReceiptNotifier stockReceiptNotifier;

	private final BusinessFinanceLedgerPostingService financeLedgerPostingService;

	public StockReceiptLifecycleService(StockReceiptLifecycleJdbcRepository repo,
			SystemLogJdbcRepository systemLogJdbcRepository, ObjectMapper objectMapper,
			StockReceiptNotifier stockReceiptNotifier, BusinessFinanceLedgerPostingService financeLedgerPostingService) {
		this.repo = repo;
		this.systemLogJdbcRepository = systemLogJdbcRepository;
		this.objectMapper = objectMapper;
		this.stockReceiptNotifier = stockReceiptNotifier;
		this.financeLedgerPostingService = financeLedgerPostingService;
	}

	@Transactional
	public StockReceiptViewData create(StockReceiptCreateRequest req, Jwt jwt) {
		int staffId = StockReceiptAccessPolicy.parseUserId(jwt);
		validateSupplier(req.supplierId());
		LocalDate receiptDate = LocalDate.parse(req.receiptDate());
		validateDetails(req.details(), receiptDate, true);
		String status = mapSaveMode(req.saveMode());
		String invoice = blankToNull(req.invoiceNumber());
		BigDecimal total = sumLineTotals(req.details());

		for (int attempt = 0; attempt < RECEIPT_CODE_RETRY; attempt++) {
			String code = nextReceiptCode(receiptDate.getYear());
			try {
				long id = repo.insertReceipt(code, req.supplierId(), staffId, receiptDate, status, invoice, total,
						blankToNull(req.notes()));
				insertAllDetails(id, req.details());
				StockReceiptViewData created = loadOrThrow(id);
				if ("Pending".equals(created.status())) {
					stockReceiptNotifier.notifyPendingApproval(staffId, id, created.receiptCode());
				}
				return created;
			}
			catch (DuplicateKeyException e) {
				if (attempt == RECEIPT_CODE_RETRY - 1) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Trùng mã phiếu hoặc trùng lô trong cùng phiếu, vui lòng thử lại");
				}
			}
		}
		throw new IllegalStateException("unreachable");
	}

	@Transactional(readOnly = true)
	public StockReceiptViewData getById(long id) {
		return repo.loadView(id).orElseThrow(() -> notFound());
	}

	@Transactional
	public StockReceiptViewData patch(long id, StockReceiptPatchRequest req, Jwt jwt) {
		if (req.supplierId() == null && req.receiptDate() == null && req.invoiceNumber() == null && req.notes() == null
				&& req.details() == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một trường để cập nhật");
		}
		ReceiptHeaderLockRow h = lockOrThrow(id);
		StockReceiptAccessPolicy.assertReceiptCreator(h.staffId(), jwt);
		if (!"Draft".equals(h.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ được sửa phiếu ở trạng thái Nháp");
		}
		LocalDate receiptDate = h.receiptDate();
		if (req.receiptDate() != null) {
			try {
				receiptDate = LocalDate.parse(req.receiptDate());
			}
			catch (DateTimeParseException e) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "receiptDate không đúng định dạng YYYY-MM-DD");
			}
		}
		if (req.supplierId() != null) {
			validateSupplier(req.supplierId());
		}
		List<StockReceiptDetailRequest> newDetails = req.details();
		if (newDetails != null) {
			validateDetails(newDetails, receiptDate, true);
		}
		BigDecimal total = h.totalAmount();
		if (newDetails != null) {
			total = sumLineTotals(newDetails);
		}
		boolean setInv = req.invoiceNumber() != null;
		String invVal = req.invoiceNumber() == null ? null : blankToNull(req.invoiceNumber());
		boolean setNotes = req.notes() != null;
		String notesVal = req.notes() == null ? null : blankToNull(req.notes());
		repo.updateHeaderAllowNullInvoiceNotes(id, req.supplierId(), req.receiptDate() != null ? receiptDate : null, setInv,
				invVal, setNotes, notesVal, newDetails != null ? total : null);
		if (newDetails != null) {
			repo.deleteDetails(id);
			insertAllDetails(id, newDetails);
		}
		return loadOrThrow(id);
	}

	@Transactional
	public void delete(long id, Jwt jwt) {
		ReceiptHeaderLockRow h = lockOrThrow(id);
		if ("Pending".equals(h.status())) {
			StockReceiptAccessPolicy.assertStaffAdminOrOwnerForPendingReceiptDelete(jwt);
		}
		else if ("Draft".equals(h.status())) {
			StockReceiptAccessPolicy.assertOwnerOnlyForDraftReceiptDelete(jwt);
		}
		else {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ được xóa phiếu ở trạng thái Nháp hoặc Chờ duyệt");
		}
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		writeStockReceiptAudit(uid, "STOCK_RECEIPT_DELETE", "Xóa phiếu nhập kho " + h.receiptCode() + " (" + h.status() + ")",
				Map.of("receiptId", id, "receiptCode", h.receiptCode(), "priorStatus", h.status()));
		repo.deleteReceipt(id);
	}

	@Transactional
	public StockReceiptViewData submit(long id, Jwt jwt) {
		ReceiptHeaderLockRow h = lockOrThrow(id);
		StockReceiptAccessPolicy.assertReceiptCreator(h.staffId(), jwt);
		if (!"Draft".equals(h.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Phiếu không ở trạng thái Nháp");
		}
		if (repo.countDetails(id) == 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Không thể gửi duyệt phiếu không có dòng chi tiết");
		}
		repo.updateStatusSubmit(id);
		StockReceiptViewData submitted = loadOrThrow(id);
		stockReceiptNotifier.notifyPendingApproval(StockReceiptAccessPolicy.parseUserId(jwt), id, submitted.receiptCode());
		return submitted;
	}

	@Transactional
	public StockReceiptViewData approve(long id, StockReceiptApproveRequest req, Jwt jwt, Authentication authentication) {
		if (!StockReceiptAccessPolicy.hasAuthority(authentication, StockReceiptAccessPolicy.AUTH_CAN_APPROVE)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền phê duyệt phiếu nhập kho");
		}
		StockReceiptAccessPolicy.assertAdminOrOwnerForApproveReject(jwt);
		int approverId = StockReceiptAccessPolicy.parseUserId(jwt);
		if (!repo.warehouseLocationActive(req.inboundLocationId())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Vị trí nhập kho không tồn tại hoặc không Active");
		}
		ReceiptHeaderLockRow h = lockOrThrow(id);
		if (!"Pending".equals(h.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT,
					"Phiếu không ở trạng thái Chờ duyệt hoặc đã được phê duyệt trước đó");
		}
		var rows = repo.loadDetailsForApprove(id);
		for (var d : rows) {
			if (!d.baseUnit()) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Chỉ chấp nhận đơn vị cơ sở (is_base_unit) cho từng dòng phiếu");
			}
			BigDecimal baseBd = d.conversionRate().multiply(BigDecimal.valueOf(d.quantity())).setScale(0, RoundingMode.HALF_UP);
			if (baseBd.compareTo(BigDecimal.valueOf(Integer.MAX_VALUE)) > 0 || baseBd.compareTo(BigDecimal.ZERO) < 0) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Số lượng quy đổi không hợp lệ");
			}
			int baseQty = baseBd.intValueExact();
			String batch = blankToNull(d.batchNumber());
			var existingInv = repo.findInventoryIdForUpdate(d.productId(), req.inboundLocationId(), batch);
			if (existingInv.isPresent()) {
				repo.updateInventoryQuantity(existingInv.get(), baseQty);
			}
			else {
				repo.insertInventory(d.productId(), req.inboundLocationId(), batch, d.expiryDate(), baseQty);
			}
			int baseUnitId = repo.findBaseUnitId(d.productId()).orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST,
					"Sản phẩm không có đơn vị cơ sở: " + d.productId()));
			String note = "Phiếu " + h.receiptCode();
			repo.insertInventoryLog(d.productId(), baseQty, baseUnitId, approverId, id, req.inboundLocationId(), note);
		}
		repo.updateApprove(id, approverId);
		financeLedgerPostingService.postStockReceiptPurchaseCostIfAbsent(h.receiptDate(), (int) id, h.totalAmount(),
				h.receiptCode(), approverId);
		writeStockReceiptAudit(approverId, "STOCK_RECEIPT_APPROVE", "Phê duyệt phiếu nhập kho " + h.receiptCode(),
				Map.of("receiptId", id, "receiptCode", h.receiptCode(), "inboundLocationId", req.inboundLocationId()));
		return loadOrThrow(id);
	}

	@Transactional
	public StockReceiptViewData reject(long id, StockReceiptRejectRequest req, Jwt jwt, Authentication authentication) {
		if (!StockReceiptAccessPolicy.hasAuthority(authentication, StockReceiptAccessPolicy.AUTH_CAN_APPROVE)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền từ chối phiếu nhập kho");
		}
		StockReceiptAccessPolicy.assertAdminOrOwnerForApproveReject(jwt);
		int reviewerId = StockReceiptAccessPolicy.parseUserId(jwt);
		ReceiptHeaderLockRow h = lockOrThrow(id);
		if (!"Pending".equals(h.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Phiếu không ở trạng thái Chờ duyệt");
		}
		String reason = req.reason().trim();
		if (reason.length() < REJECT_REASON_MIN_LEN) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Lý do từ chối phải ghi rõ (tối thiểu " + REJECT_REASON_MIN_LEN + " ký tự)");
		}
		repo.updateReject(id, reviewerId, reason);
		Map<String, Object> ctx = new HashMap<>();
		ctx.put("receiptId", id);
		ctx.put("receiptCode", h.receiptCode());
		ctx.put("reason", reason);
		writeStockReceiptAudit(reviewerId, "STOCK_RECEIPT_REJECT", "Từ chối phiếu nhập kho " + h.receiptCode(), ctx);
		return loadOrThrow(id);
	}

	// --- helpers ---

	private static BusinessException notFound() {
		return new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy phiếu nhập kho yêu cầu");
	}

	private ReceiptHeaderLockRow lockOrThrow(long id) {
		return repo.lockHeader(id).orElseThrow(StockReceiptLifecycleService::notFound);
	}

	private StockReceiptViewData loadOrThrow(long id) {
		return repo.loadView(id).orElseThrow(StockReceiptLifecycleService::notFound);
	}

	private void writeStockReceiptAudit(int userId, String action, String message, Map<String, Object> context) {
		try {
			String json = context == null || context.isEmpty() ? null : objectMapper.writeValueAsString(context);
			systemLogJdbcRepository.insertStockReceiptAudit(userId, action, message, json);
		}
		catch (JsonProcessingException ignored) {
			// Không làm hỏng giao dịch nghiệp vụ nếu ghi log thất bại
		}
	}

	private void validateSupplier(int supplierId) {
		if (!repo.supplierExistsActive(supplierId)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Nhà cung cấp không tồn tại hoặc không Active");
		}
	}

	private void validateDetails(List<StockReceiptDetailRequest> details, LocalDate receiptDate, boolean requireBaseUnit) {
		Set<String> batchKeys = new HashSet<>();
		for (int i = 0; i < details.size(); i++) {
			StockReceiptDetailRequest d = details.get(i);
			String prefix = "details[" + i + "].";
			if (!repo.productActive(d.productId())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Sản phẩm không tồn tại hoặc không Active",
						Map.of(prefix + "productId", "Sản phẩm không hợp lệ"));
			}
			var unit = repo.findUnit(d.unitId(), d.productId())
					.orElseThrow(() -> new BusinessException(ApiErrorCode.BAD_REQUEST, "unitId không thuộc productId",
							Map.of(prefix + "unitId", "Đơn vị không thuộc sản phẩm")));
			if (requireBaseUnit && !unit.baseUnit()) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Chỉ chấp nhận đơn vị cơ sở (is_base_unit)",
						Map.of(prefix + "unitId", "Phải là đơn vị cơ sở"));
			}
			LocalDate exp = null;
			if (d.expiryDate() != null && !d.expiryDate().isBlank()) {
				try {
					exp = LocalDate.parse(d.expiryDate());
				}
				catch (DateTimeParseException e) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "expiryDate không đúng định dạng",
							Map.of(prefix + "expiryDate", "YYYY-MM-DD"));
				}
				if (exp.isBefore(receiptDate)) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Hạn sử dụng không được nhỏ hơn ngày nhập kho",
							Map.of(prefix + "expiryDate", "HSD phải ≥ receiptDate"));
				}
			}
			String batch = blankToNull(d.batchNumber());
			String ukey = d.productId() + "\0" + Objects.toString(batch, "");
			if (!batchKeys.add(ukey)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Trùng sản phẩm và số lô trong cùng phiếu");
			}
		}
	}

	private void insertAllDetails(long receiptId, List<StockReceiptDetailRequest> details) {
		for (StockReceiptDetailRequest d : details) {
			LocalDate exp = parseExpiryOrNull(d.expiryDate());
			repo.insertDetail(receiptId, d.productId(), d.unitId(), d.quantity(), d.costPrice(), blankToNull(d.batchNumber()),
					exp);
		}
	}

	private static LocalDate parseExpiryOrNull(String s) {
		if (s == null || s.isBlank()) {
			return null;
		}
		return LocalDate.parse(s);
	}

	private static BigDecimal sumLineTotals(List<StockReceiptDetailRequest> details) {
		BigDecimal sum = BigDecimal.ZERO;
		for (StockReceiptDetailRequest d : details) {
			sum = sum.add(d.costPrice().multiply(BigDecimal.valueOf(d.quantity())));
		}
		return sum;
	}

	private String nextReceiptCode(int year) {
		int next = repo.nextReceiptSequenceSuffix(year) + 1;
		return "PN-" + year + "-" + String.format("%04d", next);
	}

	private static String blankToNull(String s) {
		if (s == null || s.isBlank()) {
			return null;
		}
		return s.trim();
	}

	private static String mapSaveMode(String saveMode) {
		return "pending".equalsIgnoreCase(saveMode) ? "Pending" : "Draft";
	}
}
