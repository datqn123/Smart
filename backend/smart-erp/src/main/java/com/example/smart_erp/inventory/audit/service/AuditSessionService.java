package com.example.smart_erp.inventory.audit.service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.inventory.audit.AuditApplyVarianceRequest;
import com.example.smart_erp.inventory.audit.AuditLinesPatchRequest;
import com.example.smart_erp.inventory.audit.AuditScopeBody;
import com.example.smart_erp.inventory.audit.AuditSessionApproveRequest;
import com.example.smart_erp.inventory.audit.AuditSessionCancelRequest;
import com.example.smart_erp.inventory.audit.AuditSessionCompleteRequest;
import com.example.smart_erp.inventory.audit.AuditSessionCreateRequest;
import com.example.smart_erp.inventory.audit.AuditSessionPatchRequest;
import com.example.smart_erp.inventory.audit.AuditSessionRejectRequest;
import com.example.smart_erp.inventory.audit.query.AuditSessionListQuery;
import com.example.smart_erp.inventory.audit.repository.AuditSessionJdbcRepository;
import com.example.smart_erp.inventory.audit.repository.AuditSessionJdbcRepository.AuditLogItem;
import com.example.smart_erp.inventory.audit.repository.AuditSessionJdbcRepository.InventorySnapRow;
import com.example.smart_erp.inventory.audit.repository.AuditSessionJdbcRepository.LineApplyRow;
import com.example.smart_erp.inventory.audit.repository.AuditSessionJdbcRepository.SessionLockRow;
import com.example.smart_erp.inventory.audit.response.AuditApplyVarianceData;
import com.example.smart_erp.inventory.audit.response.AuditApplyVarianceLineResult;
import com.example.smart_erp.inventory.audit.response.AuditSessionDetailData;
import com.example.smart_erp.inventory.audit.response.AuditSessionListItemData;
import com.example.smart_erp.inventory.audit.response.AuditSessionListPageData;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;

@Service
public class AuditSessionService {

	private static final String ST_PENDING = "Pending";
	private static final String ST_IN_PROGRESS = "In Progress";
	private static final String ST_PENDING_OWNER = "Pending Owner Approval";
	private static final String ST_COMPLETED = "Completed";
	private static final String ST_CANCELLED = "Cancelled";
	private static final String ST_RECHECK = "Re-check";

	private static final String EVT_SUBMITTED = "SUBMITTED_FOR_APPROVAL";
	private static final String EVT_APPROVED = "APPROVED";
	private static final String EVT_REJECTED = "REJECTED";
	private static final String EVT_OWNER_RECHECK = "OWNER_RECHECK";
	private static final String EVT_SOFT_DELETED = "SOFT_DELETED";
	private static final String EVT_CANCELLED = "CANCELLED";

	private static final int REF_NOTE_MAX = 255;

	private final AuditSessionJdbcRepository repo;

	public AuditSessionService(AuditSessionJdbcRepository repo) {
		this.repo = repo;
	}

	@Transactional(readOnly = true)
	public AuditSessionListPageData list(AuditSessionListQuery q) {
		long total = repo.countList(q);
		List<AuditSessionListItemData> items = total == 0 ? List.of() : repo.loadListPage(q);
		return new AuditSessionListPageData(items, q.page(), q.limit(), total);
	}

	@Transactional(readOnly = true)
	public AuditSessionDetailData getById(long id) {
		return repo.loadDetail(Math.toIntExact(id))
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
	}

	@Transactional
	public AuditSessionDetailData create(AuditSessionCreateRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		LocalDate auditDate = LocalDate.parse(req.auditDate());
		List<InventorySnapRow> snaps = resolveScope(req.scope());
		if (snaps.isEmpty()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Không có tồn khớp phạm vi");
		}
		String locFilter = null;
		String catFilter = null;
		switch (req.scope().mode()) {
			case "by_location_ids" -> {
				var ids = req.scope().locationIds().stream().distinct().toList();
				locFilter = repo.aggregateWarehouseCodes(ids);
			}
			case "by_category_id" -> catFilter = repo.findCategoryName(req.scope().categoryId());
			case "by_inventory_ids" -> {
			}
			default -> throw new BusinessException(ApiErrorCode.BAD_REQUEST, "scope.mode không hợp lệ");
		}
		int year = auditDate.getYear();
		int sessionId = insertSessionWithCode(year, req.title(), auditDate, locFilter, catFilter, req.notes(), userId);
		for (InventorySnapRow row : snaps) {
			repo.insertLine(sessionId, row.inventoryId(), new BigDecimal(row.quantity()));
		}
		return repo.loadDetail(sessionId)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc lại đợt kiểm kê sau khi tạo"));
	}

	private int insertSessionWithCode(int year, String title, LocalDate auditDate, String locFilter,
			String catFilter, String notes, int userId) {
		int suffix = repo.nextAuditSequenceSuffix(year);
		String code = String.format("KK-%d-%04d", year, suffix);
		return repo.insertSession(code, title, auditDate, ST_PENDING, locFilter, catFilter, notes, userId);
	}

	private List<InventorySnapRow> resolveScope(AuditScopeBody scope) {
		String mode = scope.mode();
		if (!StringUtils.hasText(mode)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "scope.mode là bắt buộc");
		}
		return switch (mode) {
			case "by_location_ids" -> {
				if (scope.locationIds() == null || scope.locationIds().isEmpty()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "scope.locationIds không được rỗng");
				}
				var ids = scope.locationIds().stream().distinct().toList();
				if (repo.countLocationsActive(ids) != ids.size()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Một hoặc nhiều vị trí không tồn tại hoặc không Active",
							Map.of("locationIds", "Kiểm tra danh sách vị trí"));
				}
				yield repo.findInventoryByLocationIds(ids);
			}
			case "by_category_id" -> {
				if (scope.categoryId() == null) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "scope.categoryId là bắt buộc");
				}
				if (!repo.categoryExists(scope.categoryId())) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Danh mục không tồn tại",
							Map.of("categoryId", "Giá trị không hợp lệ"));
				}
				yield repo.findInventoryByCategoryId(scope.categoryId());
			}
			case "by_inventory_ids" -> {
				if (scope.inventoryIds() == null || scope.inventoryIds().isEmpty()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "scope.inventoryIds không được rỗng");
				}
				var ids = scope.inventoryIds().stream().distinct().toList();
				var rows = repo.findInventoryByIds(ids);
				if (rows.size() != ids.size()) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Một hoặc nhiều inventory_id không tồn tại",
							Map.of("inventoryIds", "Danh sách không khớp tồn kho"));
				}
				yield rows;
			}
			default -> throw new BusinessException(ApiErrorCode.BAD_REQUEST, "scope.mode không hợp lệ");
		};
	}

	@Transactional
	public AuditSessionDetailData patch(long id, AuditSessionPatchRequest req, Jwt jwt) {
		int sid = Math.toIntExact(id);
		if (req.title() == null && req.notes() == null && req.status() == null && req.ownerNotes() == null) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Cần ít nhất một trường để cập nhật");
		}
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		String st = lock.status();
		if (ST_CANCELLED.equals(st)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể cập nhật đợt đã hủy");
		}
		if (ST_COMPLETED.equals(st)) {
			if (ST_RECHECK.equals(req.status())) {
				StockReceiptAccessPolicy.assertOwnerOnly(jwt);
				if (repo.countLinesWithVarianceApplied(sid) > 0) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Đã áp chênh lệch: không thể mở Re-check");
				}
				String on = req.ownerNotes();
				if (!StringUtils.hasText(on)) {
					throw new BusinessException(ApiErrorCode.BAD_REQUEST, "ownerNotes là bắt buộc khi chuyển sang Re-check",
							Map.of("ownerNotes", "Nhập lý do / ghi chú Owner"));
				}
				int uid = StockReceiptAccessPolicy.parseUserId(jwt);
				repo.transitionCompletedToRecheck(sid, on.trim());
				repo.insertEvent(sid, EVT_OWNER_RECHECK, jsonNotesPayload(on.trim()), uid);
				return getById(id);
			}
			if (req.title() != null || req.notes() != null || req.status() != null || req.ownerNotes() != null) {
				throw new BusinessException(ApiErrorCode.CONFLICT,
						"Đợt đã Completed: chỉ Owner chuyển sang Re-check (PATCH status=Re-check + ownerNotes)");
			}
		}
		if (StringUtils.hasText(req.ownerNotes()) && !ST_COMPLETED.equals(st)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "ownerNotes chỉ dùng khi Owner chuyển Completed → Re-check");
		}
		if (ST_PENDING_OWNER.equals(st)) {
			if (req.status() != null) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Đang chờ Owner duyệt: không đổi status qua PATCH; dùng approve/reject");
			}
			applyMetaPatch(sid, req);
			return getById(id);
		}
		if (ST_RECHECK.equals(st)) {
			if (req.status() != null) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Trạng thái Re-check: không đổi status qua PATCH");
			}
			applyMetaPatch(sid, req);
			return getById(id);
		}
		if (!ST_PENDING.equals(st) && !ST_IN_PROGRESS.equals(st)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Không thể cập nhật đợt ở trạng thái hiện tại");
		}
		if (req.status() != null) {
			handleStaffStatusTransition(sid, st, req.status());
		}
		applyMetaPatch(sid, req);
		return getById(id);
	}

	private void applyMetaPatch(int sid, AuditSessionPatchRequest req) {
		if (req.title() != null) {
			String t = req.title().trim();
			if (t.isEmpty()) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "title không được để trống");
			}
			if (req.notes() != null) {
				repo.updateSessionMeta(sid, t, true, req.notes());
			}
			else {
				repo.updateSessionMeta(sid, t, false, null);
			}
		}
		else if (req.notes() != null) {
			repo.updateSessionMeta(sid, null, true, req.notes());
		}
	}

	private void handleStaffStatusTransition(int sid, String current, String requested) {
		if (!ST_PENDING.equals(requested) && !ST_IN_PROGRESS.equals(requested)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Giá trị status không được hỗ trợ qua PATCH",
					Map.of("status", "Chỉ Pending hoặc In Progress"));
		}
		if (ST_IN_PROGRESS.equals(requested)) {
			if (ST_PENDING.equals(current)) {
				if (repo.existsOtherInProgress(sid)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Đã tồn tại đợt kiểm kê đang In Progress");
				}
				repo.updateSessionStatus(sid, ST_IN_PROGRESS);
			}
			else if (!ST_IN_PROGRESS.equals(current)) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Chuyển trạng thái không hợp lệ");
			}
		}
		else if (ST_PENDING.equals(requested)) {
			if (ST_IN_PROGRESS.equals(current)) {
				repo.updateSessionStatus(sid, ST_PENDING);
			}
			else if (!ST_PENDING.equals(current)) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Chuyển trạng thái không hợp lệ");
			}
		}
	}

	private static String jsonNotesPayload(String s) {
		return "{\"notes\":\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", "").replace("\n", "\\n") + "\"}";
	}

	@Transactional
	public AuditSessionDetailData patchLines(long id, AuditLinesPatchRequest req) {
		int sid = Math.toIntExact(id);
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		String st = lock.status();
		if (!ST_IN_PROGRESS.equals(st) && !ST_RECHECK.equals(st)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ được ghi số khi đợt đang In Progress hoặc Re-check");
		}
		if (ST_RECHECK.equals(st) && repo.countLinesWithVarianceApplied(sid) > 0) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Đã áp chênh lệch: không chỉnh dòng kiểm kê");
		}
		var lines = req.lines();
		var seen = new HashSet<Long>();
		for (var row : lines) {
			if (!seen.add(row.lineId())) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "lineId trùng trong cùng request",
						Map.of("lines", "Các lineId phải khác nhau"));
			}
		}
		for (var row : lines) {
			if (!repo.lineBelongsToSession(row.lineId(), sid)) {
				throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dòng không thuộc đợt kiểm kê",
						Map.of("lineId", String.valueOf(row.lineId())));
			}
			boolean updateNotes = row.notes() != null;
			repo.updateLineCounted(row.lineId(), sid, row.actualQuantity(), row.notes(), updateNotes);
		}
		return getById(id);
	}

	@Transactional
	public AuditSessionDetailData complete(long id, AuditSessionCompleteRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		int sid = Math.toIntExact(id);
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		String st = lock.status();
		if (!ST_IN_PROGRESS.equals(st)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ được hoàn tất khi đợt đang In Progress");
		}
		if (req.requireAllCountedOrDefault() && repo.countUncountedLines(sid) > 0) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Còn dòng chưa đếm (is_counted)");
		}
		repo.submitForOwnerApproval(sid);
		repo.insertEvent(sid, EVT_SUBMITTED, null, userId);
		return getById(id);
	}

	@Transactional
	public AuditSessionDetailData approve(long id, AuditSessionApproveRequest req, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt);
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		int sid = Math.toIntExact(id);
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		if (!ST_PENDING_OWNER.equals(lock.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ duyệt khi đợt đang chờ Owner (Pending Owner Approval)");
		}
		repo.approveSession(sid, uid);
		String payload = req != null && StringUtils.hasText(req.notes()) ? jsonNotesPayload(req.notes().trim()) : null;
		repo.insertEvent(sid, EVT_APPROVED, payload, uid);
		return getById(id);
	}

	@Transactional
	public AuditSessionDetailData reject(long id, AuditSessionRejectRequest req, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt);
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		int sid = Math.toIntExact(id);
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		if (!ST_PENDING_OWNER.equals(lock.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ từ chối khi đợt đang chờ Owner (Pending Owner Approval)");
		}
		repo.rejectFromOwnerApproval(sid);
		String payload = req != null && StringUtils.hasText(req.notes()) ? jsonNotesPayload(req.notes().trim()) : null;
		repo.insertEvent(sid, EVT_REJECTED, payload, uid);
		return getById(id);
	}

	@Transactional
	public void softDelete(long id, Jwt jwt) {
		StockReceiptAccessPolicy.assertOwnerOnly(jwt);
		int uid = StockReceiptAccessPolicy.parseUserId(jwt);
		int sid = Math.toIntExact(id);
		repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		repo.insertEvent(sid, EVT_SOFT_DELETED, null, uid);
		repo.softDeleteSession(sid);
	}

	@Transactional
	public AuditSessionDetailData cancel(long id, AuditSessionCancelRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		int sid = Math.toIntExact(id);
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		String st = lock.status();
		if (!ST_PENDING.equals(st) && !ST_IN_PROGRESS.equals(st) && !ST_PENDING_OWNER.equals(st)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ được hủy khi đợt Pending, In Progress hoặc chờ Owner duyệt");
		}
		repo.cancelSession(sid, req.cancelReason());
		repo.insertEvent(sid, EVT_CANCELLED, jsonNotesPayload(req.cancelReason().trim()), userId);
		return getById(id);
	}

	@Transactional
	public AuditApplyVarianceData applyVariance(long id, AuditApplyVarianceRequest req, Jwt jwt) {
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		int sid = Math.toIntExact(id);
		SessionLockRow lock = repo.lockSession(sid).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy đợt kiểm kê"));
		if (!ST_COMPLETED.equals(lock.status())) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Chỉ áp chênh lệch khi đợt đã Completed");
		}
		String mode = req.modeOrDefault();
		List<LineApplyRow> loaded = repo.loadLinesToApply(sid);
		List<LineApplyRow> withVar = loaded.stream()
				.filter(r -> r.actualQty().subtract(r.systemQty()).compareTo(BigDecimal.ZERO) != 0)
				.toList();
		if (withVar.isEmpty()) {
			return new AuditApplyVarianceData(sid, List.of());
		}
		List<LineApplyRow> pending = withVar.stream().filter(r -> r.varianceAppliedAt() == null).toList();
		if (pending.isEmpty()) {
			throw new BusinessException(ApiErrorCode.CONFLICT, "Đã áp chênh lệch cho đợt này");
		}

		List<Integer> invIds = pending.stream().map(r -> Math.toIntExact(r.inventoryId())).toList();
		Map<Integer, Integer> qtyMap = repo.lockInventoryQuantities(invIds);
		List<Integer> productIds = pending.stream().map(LineApplyRow::productId).toList();
		Map<Integer, Integer> baseUnitMap = repo.findBaseUnitIdsByProductIds(productIds);

		Map<Integer, Integer> idToNewQty = new HashMap<>();
		List<AuditLogItem> logItems = new ArrayList<>();
		List<Long> appliedLineIds = new ArrayList<>();
		List<AuditApplyVarianceLineResult> results = new ArrayList<>();

		for (LineApplyRow row : pending) {
			int invId = Math.toIntExact(row.inventoryId());
			Integer oldQty = qtyMap.get(invId);
			if (oldQty == null) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Không khóa được dòng tồn kho");
			}
			int newQty = computeNewQuantity(oldQty, row, mode);
			if (newQty < 0) {
				throw new BusinessException(ApiErrorCode.CONFLICT, "Số lượng tồn sau điều chỉnh không được âm");
			}
			int delta = newQty - oldQty;
			if (delta == 0) {
				appliedLineIds.add(row.lineId());
				results.add(new AuditApplyVarianceLineResult(row.lineId(), row.inventoryId(), 0, oldQty));
				continue;
			}
			idToNewQty.put(invId, newQty);
			Integer baseUnitId = baseUnitMap.get(row.productId());
			if (baseUnitId == null) {
				throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Thiếu đơn vị cơ sở cho sản phẩm");
			}
			String note = buildApplyReferenceNote(sid, row.lineId(), req.reason());
			logItems.add(new AuditLogItem(row.productId(), delta, baseUnitId, userId, note));
			appliedLineIds.add(row.lineId());
			results.add(new AuditApplyVarianceLineResult(row.lineId(), row.inventoryId(), delta, newQty));
		}

		if (!idToNewQty.isEmpty()) {
			repo.updateInventoryQuantitiesBatch(idToNewQty);
		}
		if (!logItems.isEmpty()) {
			repo.batchInsertInventoryLogs(logItems);
		}
		if (!appliedLineIds.isEmpty()) {
			repo.setVarianceAppliedAtBatch(appliedLineIds);
		}
		return new AuditApplyVarianceData(sid, results);
	}

	private static int computeNewQuantity(int currentQty, LineApplyRow row, String mode) {
		int roundedActual = row.actualQty().setScale(0, RoundingMode.HALF_UP).intValue();
		int delta = row.actualQty().subtract(row.systemQty()).setScale(0, RoundingMode.HALF_UP).intValue();
		if ("set_actual".equals(mode)) {
			return roundedActual;
		}
		return currentQty + delta;
	}

	private static String buildApplyReferenceNote(int sessionId, long lineId, String reason) {
		String base = "auditSession=" + sessionId + ";line=" + lineId + ";" + Objects.toString(reason, "");
		if (base.length() <= REF_NOTE_MAX) {
			return base;
		}
		return base.substring(0, REF_NOTE_MAX);
	}
}
