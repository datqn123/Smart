package com.example.smart_erp.inventory.dispatch;

import java.math.BigDecimal;
import java.sql.Date;
import java.sql.Types;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.inventory.dispatch.response.StockDispatchDetailLineData;
import com.example.smart_erp.inventory.dispatch.response.StockDispatchListItemData;

@SuppressWarnings("null")
@Repository
public class StockDispatchJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public StockDispatchJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public record LockedInventoryRow(
			long id,
			int productId,
			String productName,
			String skuCode,
			int locationId,
			int quantity,
			int lineUnitId,
			int baseUnitId,
			java.math.BigDecimal lineConversionRate) {
	}

	public Optional<LockedInventoryRow> lockInventoryRowForUpdate(long inventoryId) {
		String sql = """
				SELECT i.id, i.product_id, p.name AS product_name, p.sku_code, i.location_id, i.quantity,
				       COALESCE(i.unit_id, pub.id) AS line_unit_id,
				       pub.id AS base_unit_id,
				       COALESCE(pud.conversion_rate, 1) AS line_rate
				FROM inventory i
				INNER JOIN products p ON p.id = i.product_id
				INNER JOIN productunits pub ON pub.product_id = p.id AND pub.is_base_unit = TRUE
				LEFT JOIN productunits pud ON pud.id = i.unit_id
				WHERE i.id = :id
				FOR UPDATE OF i
				""";
		return namedJdbc.query(sql, Map.of("id", inventoryId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			return Optional.of(new LockedInventoryRow(
					rs.getLong("id"),
					rs.getInt("product_id"),
					rs.getString("product_name"),
					rs.getString("sku_code"),
					rs.getInt("location_id"),
					rs.getInt("quantity"),
					rs.getInt("line_unit_id"),
					rs.getInt("base_unit_id"),
					rs.getBigDecimal("line_rate")));
		});
	}

	public void deductInventoryQuantity(long inventoryId, int deductInRowUnit) {
		namedJdbc.update(
				"UPDATE inventory SET quantity = quantity - :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("d", deductInRowUnit).addValue("id", inventoryId));
	}

	public long insertManualDispatchHeader(String tempCode, int userId, LocalDate dispatchDate, String status,
			String notes, String referenceLabel) {
		return insertDispatchHeader(tempCode, null, userId, dispatchDate, status, notes, referenceLabel);
	}

	public long insertDispatchHeader(String tempCode, Integer orderId, int userId, LocalDate dispatchDate, String status,
			String notes, String referenceLabel) {
		KeyHolder kh = new GeneratedKeyHolder();
		String sql = """
				INSERT INTO stockdispatches (dispatch_code, order_id, user_id, dispatch_date, status, notes, reference_label)
				VALUES (:code, :oid, :uid, :d, :st, :notes, :ref)
				""";
		MapSqlParameterSource p = new MapSqlParameterSource("code", tempCode)
				.addValue("oid", orderId, Types.INTEGER)
				.addValue("uid", userId)
				.addValue("d", Date.valueOf(dispatchDate))
				.addValue("st", status)
				.addValue("notes", notes, Types.VARCHAR)
				.addValue("ref", referenceLabel, Types.VARCHAR);
		namedJdbc.update(sql, p, kh, new String[] { "id" });
		Number key = kh.getKey();
		if (key == null) {
			throw new IllegalStateException("INSERT stockdispatches không trả id");
		}
		return key.longValue();
	}

	public void insertDispatchLine(long dispatchId, long inventoryId, int quantity) {
		insertDispatchLine(dispatchId, inventoryId, quantity, null);
	}

	public void insertDispatchLine(long dispatchId, long inventoryId, int quantity, BigDecimal unitPriceSnapshot) {
		MapSqlParameterSource src = new MapSqlParameterSource("did", dispatchId).addValue("inv", inventoryId)
				.addValue("q", quantity).addValue("price", unitPriceSnapshot, Types.NUMERIC);
		namedJdbc.update("""
				INSERT INTO stockdispatch_lines (dispatch_id, inventory_id, quantity, unit_price_snapshot)
				VALUES (:did, :inv, :q, :price)
				""", src);
	}

	public int deleteLinesByDispatch(long dispatchId) {
		return namedJdbc.update("DELETE FROM stockdispatch_lines WHERE dispatch_id = :did",
				Map.of("did", dispatchId));
	}

	public boolean dispatchHasPendingLines(long dispatchId) {
		Integer n = namedJdbc.queryForObject(
				"SELECT COUNT(*)::int FROM stockdispatch_lines WHERE dispatch_id = :did", Map.of("did", dispatchId),
				Integer.class);
		return n != null && n > 0;
	}

	public int countOutboundLogs(long dispatchId) {
		Integer n = namedJdbc.queryForObject(
				"""
						SELECT COUNT(*)::int FROM inventorylogs WHERE dispatch_id = :did AND action_type = 'OUTBOUND'
						""",
				Map.of("did", dispatchId), Integer.class);
		return n == null ? 0 : n;
	}

	public List<ManualLineRow> loadPendingLinesOrdered(long dispatchId) {
		return namedJdbc.query(
				"SELECT inventory_id, quantity FROM stockdispatch_lines WHERE dispatch_id = :did ORDER BY inventory_id",
				Map.of("did", dispatchId),
				(rs, rn) -> new ManualLineRow(rs.getLong("inventory_id"), rs.getInt("quantity")));
	}

	/** Dòng phiếu xuất tay + snapshot / product để tính COGS. */
	public List<DispatchCogsLineRow> loadDispatchLinesForCogs(long dispatchId) {
		String sql = """
				SELECT sdl.inventory_id,
				       sdl.quantity,
				       sdl.unit_price_snapshot,
				       i.product_id,
				       COALESCE(i.unit_id, pub.id) AS line_unit_id,
				       p.sku_code
				FROM stockdispatch_lines sdl
				INNER JOIN inventory i ON i.id = sdl.inventory_id
				INNER JOIN products p ON p.id = i.product_id
				INNER JOIN productunits pub ON pub.product_id = i.product_id AND pub.is_base_unit = TRUE
				WHERE sdl.dispatch_id = :did
				ORDER BY sdl.inventory_id
				""";
		return namedJdbc.query(sql, Map.of("did", dispatchId), (rs, rn) -> new DispatchCogsLineRow(rs.getLong("inventory_id"),
				rs.getInt("quantity"), (BigDecimal) rs.getObject("unit_price_snapshot"), rs.getInt("product_id"),
				rs.getInt("line_unit_id"), rs.getString("sku_code")));
	}

	public Optional<Integer> findOrderIdByDispatchId(long dispatchId) {
		List<Integer> ids = namedJdbc.query("SELECT order_id FROM stockdispatches WHERE id = :id",
				Map.of("id", dispatchId), (rs, rn) -> (Integer) rs.getObject("order_id"));
		return ids.isEmpty() ? Optional.empty() : Optional.ofNullable(ids.getFirst());
	}

	public Optional<DispatchLedgerMetaRow> loadDispatchLedgerMeta(long dispatchId) {
		String sql = """
				SELECT dispatch_code, dispatch_date, status
				FROM stockdispatches WHERE id = :id
				""";
		return namedJdbc.query(sql, Map.of("id", dispatchId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			return Optional.of(new DispatchLedgerMetaRow(rs.getString("dispatch_code"),
					rs.getObject("dispatch_date", LocalDate.class), rs.getString("status")));
		});
	}

	public record ManualLineRow(long inventoryId, int quantity) {
	}

	public record DispatchCogsLineRow(long inventoryId, int quantity, BigDecimal unitPriceSnapshot, int productId,
			int lineUnitId, String skuCode) {
	}

	public record DispatchLedgerMetaRow(String dispatchCode, LocalDate dispatchDate, String status) {
	}

	public record OutboundLogItem(int productId, int quantityChange, int baseUnitId, int userId, long dispatchId,
			int fromLocationId, String referenceNote) {
	}

	public Map<Long, LockedInventoryRow> lockInventoryRowsForUpdate(List<Long> inventoryIds) {
		if (inventoryIds == null || inventoryIds.isEmpty()) {
			return Map.of();
		}
		String sql = """
				SELECT i.id, i.product_id, p.name AS product_name, p.sku_code, i.location_id, i.quantity,
				       COALESCE(i.unit_id, pub.id) AS line_unit_id,
				       pub.id AS base_unit_id,
				       COALESCE(pud.conversion_rate, 1) AS line_rate
				FROM inventory i
				INNER JOIN products p ON p.id = i.product_id
				INNER JOIN productunits pub ON pub.product_id = p.id AND pub.is_base_unit = TRUE
				LEFT JOIN productunits pud ON pud.id = i.unit_id
				WHERE i.id IN (:ids)
				FOR UPDATE OF i
				""";
		List<LockedInventoryRow> rows = namedJdbc.query(sql, new MapSqlParameterSource("ids", inventoryIds),
				(rs, rn) -> new LockedInventoryRow(
						rs.getLong("id"),
						rs.getInt("product_id"),
						rs.getString("product_name"),
						rs.getString("sku_code"),
						rs.getInt("location_id"),
						rs.getInt("quantity"),
						rs.getInt("line_unit_id"),
						rs.getInt("base_unit_id"),
						rs.getBigDecimal("line_rate")));
		Map<Long, LockedInventoryRow> map = new LinkedHashMap<>();
		for (LockedInventoryRow row : rows) {
			map.put(row.id(), row);
		}
		return map;
	}

	public void deductInventoryQuantitiesBatch(Map<Long, Integer> idToDeduct) {
		if (idToDeduct == null || idToDeduct.isEmpty()) {
			return;
		}
		StringBuilder sb = new StringBuilder("UPDATE inventory SET quantity = quantity - CASE id ");
		var src = new MapSqlParameterSource();
		int i = 0;
		for (var entry : idToDeduct.entrySet()) {
			String idParam = "id" + i;
			String valParam = "v" + i;
			sb.append("WHEN :").append(idParam).append(" THEN :").append(valParam).append(" ");
			src.addValue(idParam, entry.getKey());
			src.addValue(valParam, entry.getValue());
			i++;
		}
		sb.append("END, updated_at = CURRENT_TIMESTAMP WHERE id IN (:ids)");
		src.addValue("ids", new ArrayList<>(idToDeduct.keySet()));
		namedJdbc.update(sb.toString(), src);
	}

	public void batchInsertInventoryLogsOutbound(List<OutboundLogItem> items) {
		if (items == null || items.isEmpty()) {
			return;
		}
		String sql = """
				INSERT INTO inventorylogs (
				  product_id, action_type, quantity_change, unit_id, user_id,
				  dispatch_id, receipt_id, from_location_id, to_location_id, reference_note
				) VALUES (
				  :pid, 'OUTBOUND', :qchg, :unit_id, :uid,
				  :did, NULL, :from_loc, NULL, :note
				)
				""";
		MapSqlParameterSource[] batch = new MapSqlParameterSource[items.size()];
		for (int i = 0; i < items.size(); i++) {
			OutboundLogItem it = items.get(i);
			batch[i] = new MapSqlParameterSource("pid", it.productId())
					.addValue("qchg", -it.quantityChange())
					.addValue("unit_id", it.baseUnitId())
					.addValue("uid", it.userId())
					.addValue("did", it.dispatchId())
					.addValue("from_loc", it.fromLocationId())
					.addValue("note", it.referenceNote(), Types.VARCHAR);
		}
		namedJdbc.batchUpdate(sql, batch);
	}

	public void updateDispatchCode(long dispatchId, String dispatchCode) {
		namedJdbc.update("UPDATE stockdispatches SET dispatch_code = :c, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				Map.of("c", dispatchCode, "id", dispatchId));
	}

	private static void appendFilters(StringBuilder where, MapSqlParameterSource src, String search, String status,
			String dateFrom, String dateTo, Integer creatorUserId) {
		boolean first = where.length() == 0;
		if (creatorUserId != null) {
			// Trailing space after :cb so concatenation never yields ":cbORDER..." (NamedParameterJdbcTemplate).
			where.append(first ? " WHERE " : " AND ").append("sd.user_id = :cb ");
			src.addValue("cb", creatorUserId);
			first = false;
		}
		if (search != null && !search.isBlank()) {
			where.append(first ? " WHERE " : " AND ").append("""
					(sd.dispatch_code ILIKE :s
					   OR COALESCE(so.order_code, '') ILIKE :s
					   OR COALESCE(sd.reference_label, '') ILIKE :s)
					""");
			src.addValue("s", "%" + search.trim() + "%");
			first = false;
		}
		if (status != null && !status.isBlank() && !"all".equalsIgnoreCase(status)) {
			where.append(first ? " WHERE " : " AND ").append("sd.status = :st");
			src.addValue("st", status);
			first = false;
		}
		if (dateFrom != null && !dateFrom.isBlank()) {
			where.append(first ? " WHERE " : " AND ").append("sd.dispatch_date >= CAST(:df AS date)");
			src.addValue("df", dateFrom);
			first = false;
		}
		if (dateTo != null && !dateTo.isBlank()) {
			where.append(first ? " WHERE " : " AND ").append("sd.dispatch_date <= CAST(:dt AS date)");
			src.addValue("dt", dateTo);
			first = false;
		}
	}

	private static final String ACTIVE_DISPATCH_FILTER = " WHERE sd.deleted_at IS NULL ";

	public long countDispatches(String search, String status, String dateFrom, String dateTo, Integer creatorUserId) {
		StringBuilder where = new StringBuilder(ACTIVE_DISPATCH_FILTER);
		MapSqlParameterSource src = new MapSqlParameterSource();
		appendFilters(where, src, search, status, dateFrom, dateTo, creatorUserId);
		String sql = "SELECT COUNT(*)::bigint FROM stockdispatches sd LEFT JOIN salesorders so ON so.id = sd.order_id "
				+ where;
		Long n = namedJdbc.queryForObject(sql, src, Long.class);
		return n == null ? 0L : n;
	}

	public List<StockDispatchListItemData> listDispatches(String search, String status, String dateFrom, String dateTo,
			Integer creatorUserId, int limit, int offset) {
		StringBuilder where = new StringBuilder(ACTIVE_DISPATCH_FILTER);
		MapSqlParameterSource src = new MapSqlParameterSource("lim", limit).addValue("off", offset);
		appendFilters(where, src, search, status, dateFrom, dateTo, creatorUserId);
		String sql = """
				SELECT sd.id,
				       sd.dispatch_code,
				       COALESCE(so.order_code, '—') AS order_code,
				       COALESCE(c.name, COALESCE(sd.reference_label, '—')) AS customer_name,
				       sd.dispatch_date,
				       sd.user_id AS creator_user_id,
				       (sd.order_id IS NULL) AS manual_dispatch,
				       COALESCE(u.full_name, u.email, '—') AS user_name,
				       CASE WHEN line_agg.has_lines THEN line_agg.line_count ELSE COALESCE(log_agg.log_count, 0) END AS item_count,
				       sd.status,
				       line_agg.has_lines AS has_stockdispatch_lines,
				       COALESCE(line_agg.has_shortage, false) AS has_shortage_warning
				FROM stockdispatches sd
				INNER JOIN users u ON u.id = sd.user_id
				LEFT JOIN salesorders so ON so.id = sd.order_id
				LEFT JOIN customers c ON c.id = so.customer_id
				LEFT JOIN LATERAL (
				  SELECT COUNT(*)::int AS line_count,
				         COUNT(*) > 0 AS has_lines,
				         bool_or(sdl.quantity > i.quantity) AS has_shortage
				  FROM stockdispatch_lines sdl
				  LEFT JOIN inventory i ON i.id = sdl.inventory_id
				  WHERE sdl.dispatch_id = sd.id
				) line_agg ON true
				LEFT JOIN LATERAL (
				  SELECT COUNT(*)::int AS log_count
				  FROM inventorylogs il
				  WHERE il.dispatch_id = sd.id AND il.action_type = 'OUTBOUND'
				) log_agg ON true
				"""
				+ where + """
							ORDER BY sd.id DESC
							LIMIT :lim OFFSET :off
							""";
		return namedJdbc.query(sql, src, (rs, rn) -> new StockDispatchListItemData(rs.getLong("id"),
				rs.getString("dispatch_code"),
				rs.getString("order_code"),
				rs.getString("customer_name"),
				rs.getObject("dispatch_date", LocalDate.class),
				rs.getString("user_name"),
				rs.getInt("item_count"),
				rs.getString("status"),
				rs.getInt("creator_user_id"),
				rs.getBoolean("manual_dispatch"),
				rs.getBoolean("has_stockdispatch_lines"),
				rs.getBoolean("has_shortage_warning"),
				false,
				false));
	}

	public record LockedManualDispatchRow(long id, Integer orderId, int creatorUserId, String status,
			LocalDate dispatchDate, String notes, String referenceLabel, Instant deletedAt) {
	}

	public Optional<LockedManualDispatchRow> lockManualDispatch(long dispatchId) {
		String sql = """
				SELECT sd.id,
				       sd.order_id,
				       sd.user_id,
				       sd.status,
				       sd.dispatch_date,
				       sd.notes,
				       sd.reference_label,
				       sd.deleted_at AS deleted_ts
				FROM stockdispatches sd
				WHERE sd.id = :id
				FOR UPDATE OF sd
				""";
		return namedJdbc.query(sql, Map.of("id", dispatchId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			Integer oid = (Integer) rs.getObject("order_id");
			java.sql.Timestamp del = rs.getTimestamp("deleted_ts");
			Instant delInst = del == null ? null : del.toInstant();
			return Optional.of(new LockedManualDispatchRow(
					rs.getLong("id"),
					oid,
					rs.getInt("user_id"),
					rs.getString("status"),
					rs.getObject("dispatch_date", LocalDate.class),
					rs.getString("notes"),
					rs.getString("reference_label"),
					delInst));
		});
	}

	public void updateDispatchStatus(long dispatchId, String nextStatus) {
		namedJdbc.update("""
				UPDATE stockdispatches SET status = :st, updated_at = CURRENT_TIMESTAMP WHERE id = :id
				""", Map.of("st", nextStatus, "id", dispatchId));
	}

	public void updateDispatchDate(long dispatchId, LocalDate dispatchDate) {
		namedJdbc.update("UPDATE stockdispatches SET dispatch_date = :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				Map.of("d", Date.valueOf(dispatchDate), "id", dispatchId));
	}

	public void updateDispatchNotes(long dispatchId, String notes) {
		namedJdbc.update("UPDATE stockdispatches SET notes = :n, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", dispatchId).addValue("n", notes, Types.VARCHAR));
	}

	public void updateDispatchReference(long dispatchId, String referenceLabel) {
		namedJdbc.update("""
				UPDATE stockdispatches SET reference_label = :r, updated_at = CURRENT_TIMESTAMP WHERE id = :id
				""", new MapSqlParameterSource("id", dispatchId).addValue("r", referenceLabel, Types.VARCHAR));
	}

	/** PATCH từng trường khi không null trong service; set rỗng thành blank. */


	public void markSoftDeleted(long dispatchId, int deletedByUserId, String reason) {
		namedJdbc.update("""
				UPDATE stockdispatches
				SET deleted_at = CURRENT_TIMESTAMP,
				    deleted_by_user_id = :duid,
				    delete_reason = :r,
				    updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""", Map.of("id", dispatchId, "duid", deletedByUserId, "r", reason));
	}

	public record DispatchDetailHeaderRow(long id, String dispatchCode, String orderCode, String customerName,
			LocalDate dispatchDate, int userId, String userName, String status, String notes, String referenceLabel,
			Integer orderId, Instant deletedAt, String deleteReason, Integer deletedByUserId,
			String deletedByDisplayName) {
	}

	public Optional<DispatchDetailHeaderRow> loadDispatchDetailHeader(long dispatchId) {
		String sql = """
				SELECT sd.id,
				       sd.dispatch_code,
				       COALESCE(so.order_code, '—') AS order_code,
				       COALESCE(c.name, COALESCE(sd.reference_label, '—')) AS customer_name,
				       sd.dispatch_date,
				       sd.user_id,
				       COALESCE(u.full_name, u.email, '—') AS user_name_sd,
				       sd.status,
				       sd.notes,
				       sd.reference_label,
				       sd.order_id,
				       sd.deleted_at AS del_ts,
				       sd.delete_reason,
				       sd.deleted_by_user_id,
				       COALESCE(du.full_name, du.email, '') AS deleted_by_name
				FROM stockdispatches sd
				INNER JOIN users u ON u.id = sd.user_id
				LEFT JOIN salesorders so ON so.id = sd.order_id
				LEFT JOIN customers c ON c.id = so.customer_id
				LEFT JOIN users du ON du.id = sd.deleted_by_user_id
				WHERE sd.id = :id
				""";
		return namedJdbc.query(sql, Map.of("id", dispatchId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			java.sql.Timestamp del = rs.getTimestamp("del_ts");
			Integer deletedByUid = (Integer) rs.getObject("deleted_by_user_id");
			Integer oid = (Integer) rs.getObject("order_id");
			String delReason = rs.getString("delete_reason");
			return Optional.of(new DispatchDetailHeaderRow(
					rs.getLong("id"),
					rs.getString("dispatch_code"),
					rs.getString("order_code"),
					rs.getString("customer_name"),
					rs.getObject("dispatch_date", LocalDate.class),
					rs.getInt("user_id"),
					rs.getString("user_name_sd"),
					rs.getString("status"),
					rs.getString("notes"),
					rs.getString("reference_label"),
					oid,
					del == null ? null : del.toInstant(),
					delReason,
					deletedByUid,
					rs.getString("deleted_by_name")));
		});
	}

	public boolean detailHasShortage(long dispatchId) {
		String sql = """
				SELECT EXISTS (
				  SELECT 1 FROM stockdispatch_lines sdl
				  INNER JOIN inventory i ON i.id = sdl.inventory_id
				  WHERE sdl.dispatch_id = :id AND sdl.quantity > i.quantity
				)
				""";
		Boolean b = namedJdbc.queryForObject(sql, Map.of("id", dispatchId), Boolean.class);
		return Boolean.TRUE.equals(b);
	}

	public List<StockDispatchDetailLineData> loadManualDetailLines(long dispatchId) {
		String sql = """
				SELECT sdl.id AS line_id,
				       sdl.inventory_id,
				       i.product_id AS product_id,
				       sdl.quantity,
				       i.quantity AS available_qty,
				       p.name AS product_name,
				       p.sku_code,
				       wl.warehouse_code,
				       wl.shelf_code,
				       sdl.unit_price_snapshot
				FROM stockdispatch_lines sdl
				INNER JOIN inventory i ON i.id = sdl.inventory_id
				INNER JOIN products p ON p.id = i.product_id
				LEFT JOIN warehouselocations wl ON wl.id = i.location_id
				WHERE sdl.dispatch_id = :id
				ORDER BY sdl.id
				""";
		return namedJdbc.query(sql, Map.of("id", dispatchId),
				(rs, rn) -> new StockDispatchDetailLineData(
						rs.getLong("line_id"),
						rs.getLong("inventory_id"),
						rs.getLong("product_id"),
						rs.getInt("quantity"),
						rs.getInt("available_qty"),
						rs.getInt("quantity") > rs.getInt("available_qty"),
						rs.getString("product_name"),
						rs.getString("sku_code"),
						rs.getString("warehouse_code") == null ? "—" : rs.getString("warehouse_code"),
						rs.getString("shelf_code") == null ? "—" : rs.getString("shelf_code"),
						rs.getBigDecimal("unit_price_snapshot")));
	}

	/** Chi tiết dòng từ log OUTBOUND (phiếu gắn đơn / đã trừ kho). */
	public List<StockDispatchDetailLineData> loadOutboundLinesForDispatchDetail(long dispatchId) {
		String sql = """
				SELECT il.id AS line_id,
				       0::bigint AS inventory_id,
				       il.product_id AS product_id,
				       ABS(il.quantity_change)::int AS quantity,
				       0 AS available_qty,
				       p.name AS product_name,
				       p.sku_code,
				       COALESCE(wl.warehouse_code, '—') AS warehouse_code,
				       COALESCE(wl.shelf_code, '—') AS shelf_code
				FROM inventorylogs il
				INNER JOIN products p ON p.id = il.product_id
				LEFT JOIN warehouselocations wl ON wl.id = il.from_location_id
				WHERE il.dispatch_id = :id AND il.action_type = 'OUTBOUND'
				ORDER BY il.id
				""";
		return namedJdbc.query(sql, Map.of("id", dispatchId),
				(rs, rn) -> new StockDispatchDetailLineData(rs.getLong("line_id"), rs.getLong("inventory_id"),
						rs.getLong("product_id"),
						rs.getInt("quantity"), rs.getInt("available_qty"), false, rs.getString("product_name"),
						rs.getString("sku_code"),
						rs.getString("warehouse_code") == null ? "—" : rs.getString("warehouse_code"),
						rs.getString("shelf_code") == null ? "—" : rs.getString("shelf_code"), null));
	}
}
