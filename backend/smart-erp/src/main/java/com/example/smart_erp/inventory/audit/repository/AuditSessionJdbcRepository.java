package com.example.smart_erp.inventory.audit.repository;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.sql.Types;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.inventory.audit.query.AuditSessionListQuery;
import com.example.smart_erp.inventory.audit.query.AuditSessionStatusFilter;
import com.example.smart_erp.inventory.audit.response.AuditSessionDetailData;
import com.example.smart_erp.inventory.audit.response.AuditSessionEventItemData;
import com.example.smart_erp.inventory.audit.response.AuditSessionLineItemData;
import com.example.smart_erp.inventory.audit.response.AuditSessionListItemData;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository;

/**
 * JDBC cho đợt kiểm kê — SRS Task021–028 / Flyway {@code inventoryauditsessions}, {@code inventoryauditlines}.
 */
@SuppressWarnings("null")
@Repository
public class AuditSessionJdbcRepository {

	public record SessionLockRow(int id, String status) {
	}

	public record InventorySnapRow(int inventoryId, int quantity) {
	}

	public record LineApplyRow(long lineId, long inventoryId, int productId, BigDecimal systemQty, BigDecimal actualQty,
			Timestamp varianceAppliedAt) {
	}

	public record AuditLogItem(int productId, int quantityChange, int baseUnitId, int userId, String referenceNote) {
	}

	private final NamedParameterJdbcTemplate namedJdbc;

	public AuditSessionJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public long countList(AuditSessionListQuery q) {
		Filter f = buildFilter(q);
		String sql = "SELECT COUNT(*) FROM inventoryauditsessions s " + f.joins + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	public List<AuditSessionListItemData> loadListPage(AuditSessionListQuery q) {
		Filter f = buildFilter(q);
		int offset = (q.page() - 1) * q.limit();
		String sql = """
				SELECT
				  s.id, s.audit_code, s.title, s.audit_date, s.status, s.location_filter, s.category_filter,
				  s.created_by, uc.full_name AS created_by_name, s.completed_at, uf.full_name AS completed_by_name,
				  s.created_at, s.updated_at,
				  line_agg.total_lines,
				  line_agg.counted_lines,
				  line_agg.variance_lines
				FROM inventoryauditsessions s
				INNER JOIN users uc ON uc.id = s.created_by
				LEFT JOIN users uf ON uf.id = s.completed_by
				LEFT JOIN LATERAL (
				  SELECT COUNT(*)::int AS total_lines,
				         COUNT(*) FILTER (WHERE l.is_counted)::int AS counted_lines,
				         COUNT(*) FILTER (WHERE l.is_counted AND l.actual_quantity IS NOT NULL AND (l.actual_quantity - l.system_quantity) <> 0)::int AS variance_lines
				  FROM inventoryauditlines l
				  WHERE l.session_id = s.id
				) line_agg ON true
				""" + f.joins + f.where + " ORDER BY s.id ASC LIMIT " + q.limit() + " OFFSET " + offset;
		return namedJdbc.query(sql, f.source, LIST_ROW);
	}

	public int insertSession(String auditCode, String title, LocalDate auditDate, String status, String locationFilter,
			String categoryFilter, String notes, int createdBy) {
		String sql = """
				INSERT INTO inventoryauditsessions (audit_code, title, audit_date, status, location_filter, category_filter, notes, created_by)
				VALUES (:audit_code, :title, :audit_date, :status, :location_filter, :category_filter, :notes, :created_by)
				RETURNING id
				""";
		Integer id = namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("audit_code", auditCode).addValue("title", title)
						.addValue("audit_date", java.sql.Date.valueOf(auditDate)).addValue("status", status)
						.addValue("location_filter", locationFilter, Types.VARCHAR)
						.addValue("category_filter", categoryFilter, Types.VARCHAR).addValue("notes", notes, Types.VARCHAR)
						.addValue("created_by", createdBy),
				Integer.class);
		if (id == null) {
			throw new IllegalStateException("INSERT inventoryauditsessions không trả id");
		}
		return id;
	}

	public void insertLine(int sessionId, int inventoryId, BigDecimal systemQuantity) {
		String sql = """
				INSERT INTO inventoryauditlines (session_id, inventory_id, system_quantity, is_counted)
				VALUES (:sid, :iid, :sq, FALSE)
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("sid", sessionId).addValue("iid", inventoryId).addValue("sq", systemQuantity));
	}

	public Optional<SessionLockRow> lockSession(int sessionId) {
		String sql = "SELECT id, status FROM inventoryauditsessions WHERE id = :id AND deleted_at IS NULL FOR UPDATE";
		var list = namedJdbc.query(sql, new MapSqlParameterSource("id", sessionId),
				(rs, i) -> new SessionLockRow(rs.getInt("id"), rs.getString("status")));
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public boolean existsOtherInProgress(int excludeSessionId) {
		String sql = """
				SELECT EXISTS(
				  SELECT 1 FROM inventoryauditsessions s
				  WHERE s.status = 'In Progress' AND s.deleted_at IS NULL AND s.id <> :ex
				)
				""";
		Boolean b = namedJdbc.queryForObject(sql, new MapSqlParameterSource("ex", excludeSessionId), Boolean.class);
		return Boolean.TRUE.equals(b);
	}

	public List<InventorySnapRow> findInventoryByLocationIds(List<Integer> locationIds) {
		String sql = "SELECT i.id, i.quantity FROM inventory i WHERE i.location_id IN (:ids) ORDER BY i.id";
		return namedJdbc.query(sql, new MapSqlParameterSource("ids", locationIds),
				(rs, i) -> new InventorySnapRow(rs.getInt("id"), rs.getInt("quantity")));
	}

	public List<InventorySnapRow> findInventoryByCategoryId(int categoryId) {
		String sql = """
				SELECT i.id, i.quantity FROM inventory i
				INNER JOIN products p ON p.id = i.product_id
				WHERE p.category_id = :cid
				ORDER BY i.id
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource("cid", categoryId),
				(rs, i) -> new InventorySnapRow(rs.getInt("id"), rs.getInt("quantity")));
	}

	public List<InventorySnapRow> findInventoryByIds(List<Integer> inventoryIds) {
		String sql = "SELECT i.id, i.quantity FROM inventory i WHERE i.id IN (:ids) ORDER BY i.id";
		return namedJdbc.query(sql, new MapSqlParameterSource("ids", inventoryIds),
				(rs, i) -> new InventorySnapRow(rs.getInt("id"), rs.getInt("quantity")));
	}

	public int countLocationsActive(List<Integer> ids) {
		if (ids.isEmpty()) {
			return 0;
		}
		Integer c = namedJdbc.queryForObject(
				"SELECT COUNT(*)::int FROM warehouselocations wl WHERE wl.id IN (:ids) AND wl.status = 'Active'",
				new MapSqlParameterSource("ids", ids), Integer.class);
		return c != null ? c : 0;
	}

	public boolean categoryExists(int categoryId) {
		Integer one = namedJdbc.queryForObject("SELECT 1 FROM categories WHERE id = :id LIMIT 1",
				new MapSqlParameterSource("id", categoryId), Integer.class);
		return one != null;
	}

	public String aggregateWarehouseCodes(List<Integer> locationIds) {
		if (locationIds.isEmpty()) {
			return null;
		}
		String sql = "SELECT string_agg(DISTINCT wl.warehouse_code, ', ' ORDER BY wl.warehouse_code) FROM warehouselocations wl WHERE wl.id IN (:ids)";
		return namedJdbc.queryForObject(sql, new MapSqlParameterSource("ids", locationIds), String.class);
	}

	public String findCategoryName(int categoryId) {
		return namedJdbc.queryForObject("SELECT name FROM categories WHERE id = :id",
				new MapSqlParameterSource("id", categoryId), String.class);
	}

	public void updateSessionMeta(int sessionId, String title, Boolean setNotes, String notes) {
		StringBuilder sb = new StringBuilder("UPDATE inventoryauditsessions SET updated_at = CURRENT_TIMESTAMP");
		var src = new MapSqlParameterSource("id", sessionId);
		if (title != null) {
			sb.append(", title = :title");
			src.addValue("title", title);
		}
		if (Boolean.TRUE.equals(setNotes)) {
			sb.append(", notes = :notes");
			src.addValue("notes", notes, Types.VARCHAR);
		}
		sb.append(" WHERE id = :id");
		namedJdbc.update(sb.toString(), src);
	}

	public void updateSessionStatus(int sessionId, String newStatus) {
		namedJdbc.update("UPDATE inventoryauditsessions SET status = :st, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", sessionId).addValue("st", newStatus));
	}

	public void submitForOwnerApproval(int sessionId) {
		namedJdbc.update(
				"UPDATE inventoryauditsessions SET status = 'Pending Owner Approval', updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", sessionId));
	}

	public void approveSession(int sessionId, int completedByUserId) {
		String sql = """
				UPDATE inventoryauditsessions SET
				  status = 'Completed',
				  completed_at = CURRENT_TIMESTAMP,
				  completed_by = :uid,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("id", sessionId).addValue("uid", completedByUserId));
	}

	public void rejectFromOwnerApproval(int sessionId) {
		namedJdbc.update(
				"UPDATE inventoryauditsessions SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", sessionId));
	}

	public void softDeleteSession(int sessionId) {
		namedJdbc.update(
				"UPDATE inventoryauditsessions SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND deleted_at IS NULL",
				new MapSqlParameterSource("id", sessionId));
	}

	public int countLinesWithVarianceApplied(int sessionId) {
		Integer c = namedJdbc.queryForObject(
				"SELECT COUNT(*)::int FROM inventoryauditlines WHERE session_id = :id AND variance_applied_at IS NOT NULL",
				new MapSqlParameterSource("id", sessionId), Integer.class);
		return c != null ? c : 0;
	}

	public void transitionCompletedToRecheck(int sessionId, String ownerNotes) {
		String sql = """
				UPDATE inventoryauditsessions SET
				  status = 'Re-check',
				  owner_notes = :on,
				  completed_at = NULL,
				  completed_by = NULL,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("id", sessionId).addValue("on", ownerNotes, Types.VARCHAR));
	}

	public void insertEvent(int sessionId, String eventType, String payloadJson, int createdBy) {
		if (payloadJson != null) {
			String sql = """
					INSERT INTO inventory_audit_session_events (session_id, event_type, payload, created_by)
					VALUES (:sid, :etype, CAST(:payload AS jsonb), :uid)
					""";
			namedJdbc.update(sql, new MapSqlParameterSource("sid", sessionId).addValue("etype", eventType)
					.addValue("payload", payloadJson).addValue("uid", createdBy));
		}
		else {
			String sql = """
					INSERT INTO inventory_audit_session_events (session_id, event_type, payload, created_by)
					VALUES (:sid, :etype, NULL, :uid)
					""";
			namedJdbc.update(sql,
					new MapSqlParameterSource("sid", sessionId).addValue("etype", eventType).addValue("uid", createdBy));
		}
	}

	public List<AuditSessionEventItemData> listEvents(int sessionId) {
		String sql = """
				SELECT id, event_type, payload::text AS payload_text, created_by, created_at
				FROM inventory_audit_session_events
				WHERE session_id = :sid
				ORDER BY id ASC
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource("sid", sessionId), EVENT_ROW);
	}

	public void cancelSession(int sessionId, String cancelReason) {
		namedJdbc.update(
				"UPDATE inventoryauditsessions SET status = 'Cancelled', cancel_reason = :cr, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", sessionId).addValue("cr", cancelReason, Types.VARCHAR));
	}

	public int countUncountedLines(int sessionId) {
		Integer c = namedJdbc.queryForObject(
				"SELECT COUNT(*)::int FROM inventoryauditlines WHERE session_id = :id AND is_counted = FALSE",
				new MapSqlParameterSource("id", sessionId), Integer.class);
		return c != null ? c : 0;
	}

	public void updateLineCounted(long lineId, int sessionId, BigDecimal actualQty, String notes, boolean updateNotes) {
		StringBuilder sb = new StringBuilder("""
				UPDATE inventoryauditlines SET
				  actual_quantity = :aq,
				  is_counted = TRUE,
				  updated_at = CURRENT_TIMESTAMP
				""");
		var src = new MapSqlParameterSource("lid", lineId).addValue("sid", sessionId).addValue("aq", actualQty);
		if (updateNotes) {
			sb.append(", notes = :notes");
			src.addValue("notes", notes, Types.VARCHAR);
		}
		sb.append(" WHERE id = :lid AND session_id = :sid");
		int n = namedJdbc.update(sb.toString(), src);
		if (n != 1) {
			throw new IllegalStateException("UPDATE line không khớp");
		}
	}

	public boolean lineBelongsToSession(long lineId, int sessionId) {
		Integer one = namedJdbc.queryForObject(
				"SELECT 1 FROM inventoryauditlines WHERE id = :lid AND session_id = :sid LIMIT 1",
				new MapSqlParameterSource("lid", lineId).addValue("sid", sessionId), Integer.class);
		return one != null;
	}

	public List<LineApplyRow> loadLinesToApply(int sessionId) {
		String sql = """
				SELECT l.id, l.inventory_id, i.product_id, l.system_quantity, l.actual_quantity, l.variance_applied_at
				FROM inventoryauditlines l
				INNER JOIN inventory i ON i.id = l.inventory_id
				WHERE l.session_id = :sid AND l.is_counted = TRUE AND l.actual_quantity IS NOT NULL
				ORDER BY l.id
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource("sid", sessionId), LINE_APPLY_ROW);
	}

	public Optional<Integer> lockInventoryQuantity(int inventoryId) {
		String sql = "SELECT quantity FROM inventory WHERE id = :id FOR UPDATE";
		List<Integer> rows = namedJdbc.query(sql, new MapSqlParameterSource("id", inventoryId),
				(rs, i) -> rs.getInt("quantity"));
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public void updateInventoryQuantity(int inventoryId, int newQty) {
		namedJdbc.update("UPDATE inventory SET quantity = :q, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("q", newQty).addValue("id", inventoryId));
	}

	public void insertInventoryLog(int productId, int quantityChange, int baseUnitId, Integer userId, String referenceNote) {
		String sql = """
				INSERT INTO inventorylogs (product_id, action_type, quantity_change, unit_id, user_id, dispatch_id, receipt_id, from_location_id, to_location_id, reference_note)
				VALUES (:pid, 'ADJUSTMENT', :qchg, :uid_unit, :user_id, NULL, NULL, NULL, NULL, :note)
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("pid", productId).addValue("qchg", quantityChange).addValue("uid_unit", baseUnitId)
						.addValue("user_id", userId, Types.INTEGER).addValue("note", referenceNote, Types.VARCHAR));
	}

	public void setVarianceAppliedAt(long lineId) {
		namedJdbc.update("UPDATE inventoryauditlines SET variance_applied_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", lineId));
	}

	public int nextAuditSequenceSuffix(int year) {
		String seqName = "inventoryauditsessions_seq_" + year;
		namedJdbc.getJdbcTemplate().execute("CREATE SEQUENCE IF NOT EXISTS " + seqName);
		Integer n = namedJdbc.queryForObject("SELECT nextval('" + seqName + "')", new MapSqlParameterSource(), Integer.class);
		return n != null ? n : 0;
	}

	public Map<Integer, Integer> lockInventoryQuantities(List<Integer> inventoryIds) {
		if (inventoryIds == null || inventoryIds.isEmpty()) {
			return Map.of();
		}
		String sql = "SELECT id, quantity FROM inventory WHERE id IN (:ids) FOR UPDATE";
		List<Map<String, Object>> rows = namedJdbc.queryForList(sql, new MapSqlParameterSource("ids", inventoryIds));
		Map<Integer, Integer> map = new LinkedHashMap<>();
		for (Map<String, Object> row : rows) {
			map.put((Integer) row.get("id"), (Integer) row.get("quantity"));
		}
		return map;
	}

	public void updateInventoryQuantitiesBatch(Map<Integer, Integer> idToNewQty) {
		if (idToNewQty == null || idToNewQty.isEmpty()) {
			return;
		}
		StringBuilder sb = new StringBuilder("UPDATE inventory SET quantity = CASE id ");
		var src = new MapSqlParameterSource();
		int i = 0;
		for (var entry : idToNewQty.entrySet()) {
			String idParam = "id" + i;
			String valParam = "v" + i;
			sb.append("WHEN :").append(idParam).append(" THEN :").append(valParam).append(" ");
			src.addValue(idParam, entry.getKey());
			src.addValue(valParam, entry.getValue());
			i++;
		}
		sb.append("END, updated_at = CURRENT_TIMESTAMP WHERE id IN (:ids)");
		src.addValue("ids", new ArrayList<>(idToNewQty.keySet()));
		namedJdbc.update(sb.toString(), src);
	}

	public Map<Integer, Integer> findBaseUnitIdsByProductIds(List<Integer> productIds) {
		if (productIds == null || productIds.isEmpty()) {
			return Map.of();
		}
		String sql = "SELECT id, product_id FROM productunits WHERE product_id IN (:pids) AND is_base_unit = TRUE";
		List<Map<String, Object>> rows = namedJdbc.queryForList(sql, new MapSqlParameterSource("pids", productIds));
		Map<Integer, Integer> map = new HashMap<>();
		for (Map<String, Object> row : rows) {
			map.put((Integer) row.get("product_id"), (Integer) row.get("id"));
		}
		return map;
	}

	public void batchInsertInventoryLogs(List<AuditLogItem> items) {
		if (items == null || items.isEmpty()) {
			return;
		}
		String sql = """
				INSERT INTO inventorylogs (product_id, action_type, quantity_change, unit_id, user_id, dispatch_id, receipt_id, from_location_id, to_location_id, reference_note)
				VALUES (:pid, 'ADJUSTMENT', :qchg, :unit_id, :user_id, NULL, NULL, NULL, NULL, :note)
				""";
		MapSqlParameterSource[] batch = new MapSqlParameterSource[items.size()];
		for (int i = 0; i < items.size(); i++) {
			AuditLogItem it = items.get(i);
			batch[i] = new MapSqlParameterSource("pid", it.productId())
					.addValue("qchg", it.quantityChange())
					.addValue("unit_id", it.baseUnitId())
					.addValue("user_id", it.userId(), Types.INTEGER)
					.addValue("note", it.referenceNote(), Types.VARCHAR);
		}
		namedJdbc.batchUpdate(sql, batch);
	}

	public void setVarianceAppliedAtBatch(List<Long> lineIds) {
		if (lineIds == null || lineIds.isEmpty()) {
			return;
		}
		namedJdbc.update("UPDATE inventoryauditlines SET variance_applied_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id IN (:ids)",
				new MapSqlParameterSource("ids", lineIds));
	}

	public Optional<Integer> findBaseUnitId(int productId) {
		List<Integer> ids = namedJdbc.query(
				"SELECT id FROM productunits WHERE product_id = :pid AND is_base_unit = TRUE LIMIT 1",
				new MapSqlParameterSource("pid", productId), (rs, i) -> rs.getInt("id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public Optional<AuditSessionDetailData> loadDetail(int sessionId) {
		String hsql = """
				SELECT s.id, s.audit_code, s.title, s.audit_date, s.status, s.location_filter, s.category_filter, s.notes,
				  s.created_by, uc.full_name AS created_by_name, s.completed_at, uf.full_name AS completed_by_name,
				  s.cancel_reason, s.created_at, s.updated_at, s.owner_notes
				FROM inventoryauditsessions s
				INNER JOIN users uc ON uc.id = s.created_by
				LEFT JOIN users uf ON uf.id = s.completed_by
				WHERE s.id = :id AND s.deleted_at IS NULL
				""";
		List<HeaderRow> headers = namedJdbc.query(hsql, new MapSqlParameterSource("id", sessionId), HEADER_ROW);
		if (headers.isEmpty()) {
			return Optional.empty();
		}
		HeaderRow hr = headers.getFirst();
		String lsql = """
				SELECT l.id, l.session_id, i.id AS inventory_id, p.id AS product_id, p.name AS product_name, p.sku_code,
				  pu.unit_name, i.location_id, wl.warehouse_code, wl.shelf_code, i.batch_number,
				  l.system_quantity, l.actual_quantity, l.is_counted, l.notes
				FROM inventoryauditlines l
				INNER JOIN inventory i ON i.id = l.inventory_id
				INNER JOIN products p ON p.id = i.product_id
				INNER JOIN warehouselocations wl ON wl.id = i.location_id
				INNER JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
				WHERE l.session_id = :sid
				ORDER BY l.id
				""";
		List<AuditSessionLineItemData> lines = namedJdbc.query(lsql, new MapSqlParameterSource("sid", sessionId), DETAIL_LINE);
		List<AuditSessionEventItemData> events = listEvents(sessionId);
		return Optional.of(new AuditSessionDetailData(hr.id(), hr.auditCode(), hr.title(), hr.auditDate(), hr.status(), hr.locationFilter(),
				hr.categoryFilter(), hr.notes(), hr.createdBy(), hr.createdByName(), hr.completedAt(), hr.completedByName(), hr.cancelReason(),
				hr.createdAt(), hr.updatedAt(), hr.ownerNotes(), events, lines));
	}

	private record HeaderRow(long id, String auditCode, String title, LocalDate auditDate, String status, String locationFilter,
			String categoryFilter, String notes, int createdBy, String createdByName, Instant completedAt, String completedByName,
			String cancelReason, Instant createdAt, Instant updatedAt, String ownerNotes) {
	}

	private static final RowMapper<HeaderRow> HEADER_ROW = (rs, i) -> new HeaderRow(rs.getLong("id"), rs.getString("audit_code"),
			rs.getString("title"), rs.getObject("audit_date", LocalDate.class), rs.getString("status"), rs.getString("location_filter"),
			rs.getString("category_filter"), rs.getString("notes"), rs.getInt("created_by"), rs.getString("created_by_name"),
			toInstant(rs.getTimestamp("completed_at")), rs.getString("completed_by_name"), rs.getString("cancel_reason"),
			toInstantNonNull(rs.getTimestamp("created_at")), toInstantNonNull(rs.getTimestamp("updated_at")), rs.getString("owner_notes"));

	private static final RowMapper<AuditSessionEventItemData> EVENT_ROW = (rs, i) -> new AuditSessionEventItemData(rs.getLong("id"),
			rs.getString("event_type"), rs.getString("payload_text"), rs.getInt("created_by"), toInstantNonNull(rs.getTimestamp("created_at")));

	private static final RowMapper<AuditSessionListItemData> LIST_ROW = (rs, i) -> new AuditSessionListItemData(rs.getLong("id"),
			rs.getString("audit_code"), rs.getString("title"), rs.getObject("audit_date", LocalDate.class), rs.getString("status"),
			rs.getString("location_filter"), rs.getString("category_filter"), rs.getInt("created_by"), rs.getString("created_by_name"),
			toInstant(rs.getTimestamp("completed_at")), rs.getString("completed_by_name"), toInstantNonNull(rs.getTimestamp("created_at")),
			toInstantNonNull(rs.getTimestamp("updated_at")), rs.getInt("total_lines"), rs.getInt("counted_lines"),
			rs.getInt("variance_lines"));

	private static final RowMapper<AuditSessionLineItemData> DETAIL_LINE = (rs, i) -> {
		BigDecimal system = rs.getBigDecimal("system_quantity");
		BigDecimal actual = rs.getBigDecimal("actual_quantity");
		boolean counted = rs.getBoolean("is_counted");
		BigDecimal variance = BigDecimal.ZERO;
		BigDecimal pct = null;
		if (counted && actual != null) {
			variance = actual.subtract(system);
			if (system.compareTo(BigDecimal.ZERO) != 0) {
				pct = variance.divide(system, 4, java.math.RoundingMode.HALF_UP).multiply(new BigDecimal("100"));
			}
		}
		return new AuditSessionLineItemData(rs.getLong("id"), rs.getLong("session_id"), rs.getLong("inventory_id"),
				rs.getInt("product_id"), rs.getString("product_name"), rs.getString("sku_code"), rs.getString("unit_name"),
				rs.getInt("location_id"), rs.getString("warehouse_code"), rs.getString("shelf_code"), rs.getString("batch_number"),
				system, actual, variance, pct, counted, rs.getString("notes"));
	};

	private static final RowMapper<LineApplyRow> LINE_APPLY_ROW = (rs, i) -> new LineApplyRow(rs.getLong("id"), rs.getLong("inventory_id"),
			rs.getInt("product_id"), rs.getBigDecimal("system_quantity"), rs.getBigDecimal("actual_quantity"),
			rs.getTimestamp("variance_applied_at"));

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : null;
	}

	private static Instant toInstantNonNull(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	private Filter buildFilter(AuditSessionListQuery q) {
		StringBuilder where = new StringBuilder(" WHERE s.deleted_at IS NULL");
		var src = new MapSqlParameterSource();
		if (q.status() != AuditSessionStatusFilter.ALL) {
			where.append(" AND s.status = :_status");
			src.addValue("_status", q.status().sqlLiteralOrNull());
		}
		if (q.search() != null) {
			where.append(
					" AND (s.audit_code ILIKE :_search OR s.title ILIKE :_search OR EXISTS (SELECT 1 FROM users u WHERE u.id = s.created_by AND u.full_name ILIKE :_search))");
			src.addValue("_search", InventoryListJdbcRepository.buildSearchPattern(q.search()));
		}
		if (q.dateFrom() != null) {
			where.append(" AND s.audit_date >= :_df");
			src.addValue("_df", q.dateFrom());
		}
		if (q.dateTo() != null) {
			where.append(" AND s.audit_date <= :_dt");
			src.addValue("_dt", q.dateTo());
		}
		return new Filter("", where.toString(), src);
	}

	private record Filter(String joins, String where, MapSqlParameterSource source) {
	}
}
