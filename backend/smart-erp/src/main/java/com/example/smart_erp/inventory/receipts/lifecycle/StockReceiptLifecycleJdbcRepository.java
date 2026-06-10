package com.example.smart_erp.inventory.receipts.lifecycle;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.sql.Types;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.inventory.receipts.response.StockReceiptLineViewData;
import com.example.smart_erp.inventory.receipts.response.StockReceiptViewData;

/**
 * JDBC cho vòng đời phiếu nhập (Task014–020).
 */
@SuppressWarnings("null")
@Repository
public class StockReceiptLifecycleJdbcRepository {

	public record ReceiptHeaderLockRow(long id, String receiptCode, long supplierId, int staffId, LocalDate receiptDate,
			String status, String invoiceNumber, BigDecimal totalAmount, String notes) {
	}

	public record UnitRow(int id, int productId, boolean baseUnit, BigDecimal conversionRate) {
	}

	private final NamedParameterJdbcTemplate namedJdbc;

	public StockReceiptLifecycleJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public Optional<ReceiptHeaderLockRow> lockHeader(long receiptId) {
		String sql = """
				SELECT sr.id, sr.receipt_code, sr.supplier_id, sr.staff_id, sr.receipt_date, sr.status,
				  sr.invoice_number, sr.total_amount, sr.notes
				FROM stockreceipts sr WHERE sr.id = :id FOR UPDATE
				""";
		var list = namedJdbc.query(sql, new MapSqlParameterSource("id", receiptId), HEADER_LOCK_ROW);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public int nextReceiptSequenceSuffix(int year) {
		String sql = """
				SELECT COALESCE(MAX(split_part(sr.receipt_code, '-', 3)::int), 0)
				FROM stockreceipts sr
				WHERE sr.receipt_code LIKE 'PN-' || CAST(:y AS text) || '-%'
				""";
		Integer n = namedJdbc.queryForObject(sql, new MapSqlParameterSource("y", year), Integer.class);
		return n != null ? n : 0;
	}

	public long insertReceipt(String receiptCode, int supplierId, int staffId, LocalDate receiptDate, String status,
			String invoiceNumber, BigDecimal totalAmount, String notes) {
		String sql = """
				INSERT INTO stockreceipts (receipt_code, supplier_id, staff_id, receipt_date, status, invoice_number, total_amount, notes)
				VALUES (:receipt_code, :supplier_id, :staff_id, :receipt_date, :status, :invoice_number, :total_amount, :notes)
				RETURNING id
				""";
		Long id = namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("receipt_code", receiptCode).addValue("supplier_id", supplierId)
						.addValue("staff_id", staffId).addValue("receipt_date", java.sql.Date.valueOf(receiptDate))
						.addValue("status", status).addValue("invoice_number", invoiceNumber, Types.VARCHAR)
						.addValue("total_amount", totalAmount).addValue("notes", notes, Types.VARCHAR),
				Long.class);
		if (id == null) {
			throw new IllegalStateException("INSERT stockreceipts không trả id");
		}
		return id;
	}

	public void insertDetail(long receiptId, int productId, int unitId, int quantity, BigDecimal costPrice,
			String batchNumber, LocalDate expiryDate) {
		String sql = """
				INSERT INTO stockreceiptdetails (receipt_id, product_id, unit_id, quantity, cost_price, batch_number, expiry_date)
				VALUES (:receipt_id, :product_id, :unit_id, :quantity, :cost_price, :batch_number, :expiry_date)
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("receipt_id", receiptId).addValue("product_id", productId)
						.addValue("unit_id", unitId).addValue("quantity", quantity).addValue("cost_price", costPrice)
						.addValue("batch_number", batchNumber, Types.VARCHAR)
						.addValue("expiry_date", expiryDate != null ? java.sql.Date.valueOf(expiryDate) : null,
								Types.DATE));
	}

	public void deleteDetails(long receiptId) {
		namedJdbc.update("DELETE FROM stockreceiptdetails WHERE receipt_id = :id", new MapSqlParameterSource("id", receiptId));
	}

	/** PATCH: set invoice_number / notes to NULL khi client gửi chuỗi rỗng (đã chuẩn hoá ở service). */
	public void updateHeaderAllowNullInvoiceNotes(long receiptId, Integer supplierId, LocalDate receiptDate,
			Boolean setInvoiceNumber, String invoiceNumber, Boolean setNotes, String notes, BigDecimal totalAmount) {
		// Đơn giản: luôn set các cột đã quyết định ở service layer qua cờ
		StringBuilder sb = new StringBuilder("UPDATE stockreceipts SET updated_at = CURRENT_TIMESTAMP");
		var src = new MapSqlParameterSource("id", receiptId);
		if (supplierId != null) {
			sb.append(", supplier_id = :supplier_id");
			src.addValue("supplier_id", supplierId);
		}
		if (receiptDate != null) {
			sb.append(", receipt_date = :receipt_date");
			src.addValue("receipt_date", java.sql.Date.valueOf(receiptDate));
		}
		if (Boolean.TRUE.equals(setInvoiceNumber)) {
			sb.append(", invoice_number = :invoice_number");
			src.addValue("invoice_number", invoiceNumber, Types.VARCHAR);
		}
		if (Boolean.TRUE.equals(setNotes)) {
			sb.append(", notes = :notes");
			src.addValue("notes", notes, Types.VARCHAR);
		}
		if (totalAmount != null) {
			sb.append(", total_amount = :total_amount");
			src.addValue("total_amount", totalAmount);
		}
		sb.append(" WHERE id = :id");
		namedJdbc.update(sb.toString(), src);
	}

	public void deleteReceipt(long receiptId) {
		namedJdbc.update("DELETE FROM stockreceipts WHERE id = :id", new MapSqlParameterSource("id", receiptId));
	}

	public void updateStatusSubmit(long receiptId) {
		namedJdbc.update(
				"UPDATE stockreceipts SET status = 'Pending', updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("id", receiptId));
	}

	public void updateApprove(long receiptId, int approverUserId) {
		String sql = """
				UPDATE stockreceipts SET
				  status = 'Approved',
				  approved_by = :uid,
				  approved_at = CURRENT_TIMESTAMP,
				  reviewed_by = :uid,
				  reviewed_at = CURRENT_TIMESTAMP,
				  rejection_reason = NULL,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("id", receiptId).addValue("uid", approverUserId));
	}

	public void updateReject(long receiptId, int reviewerUserId, String reason) {
		String sql = """
				UPDATE stockreceipts SET
				  status = 'Rejected',
				  rejection_reason = :reason,
				  reviewed_by = :uid,
				  reviewed_at = CURRENT_TIMESTAMP,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("id", receiptId).addValue("uid", reviewerUserId).addValue("reason", reason));
	}

	public int countDetails(long receiptId) {
		Integer c = namedJdbc.queryForObject("SELECT COUNT(*)::int FROM stockreceiptdetails WHERE receipt_id = :id",
				new MapSqlParameterSource("id", receiptId), Integer.class);
		return c != null ? c : 0;
	}

	public boolean supplierExistsActive(int supplierId) {
		Integer one = namedJdbc.queryForObject(
				"SELECT 1 FROM suppliers WHERE id = :id AND status = 'Active' LIMIT 1",
				new MapSqlParameterSource("id", supplierId), Integer.class);
		return one != null;
	}

	public boolean productActive(int productId) {
		Integer one = namedJdbc.queryForObject(
				"SELECT 1 FROM products WHERE id = :id AND status = 'Active' LIMIT 1",
				new MapSqlParameterSource("id", productId), Integer.class);
		return one != null;
	}

	public Optional<UnitRow> findUnit(int unitId, int productId) {
		String sql = """
				SELECT pu.id, pu.product_id, pu.is_base_unit, pu.conversion_rate
				FROM productunits pu WHERE pu.id = :uid AND pu.product_id = :pid
				""";
		var list = namedJdbc.query(sql, new MapSqlParameterSource("uid", unitId).addValue("pid", productId), UNIT_ROW);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public Optional<Integer> findBaseUnitId(int productId) {
		String sql = "SELECT id FROM productunits WHERE product_id = :pid AND is_base_unit = TRUE LIMIT 1";
		List<Integer> ids = namedJdbc.query(sql, new MapSqlParameterSource("pid", productId),
				(rs, i) -> rs.getInt("id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public boolean warehouseLocationActive(int locationId) {
		Integer one = namedJdbc.queryForObject(
				"SELECT 1 FROM warehouselocations WHERE id = :id AND status = 'Active' LIMIT 1",
				new MapSqlParameterSource("id", locationId), Integer.class);
		return one != null;
	}

	public List<ApproveDetailRow> loadDetailsForApprove(long receiptId) {
		String sql = """
				SELECT d.product_id, d.unit_id, d.quantity, d.cost_price, d.batch_number, d.expiry_date, pu.conversion_rate, pu.is_base_unit
				FROM stockreceiptdetails d
				INNER JOIN productunits pu ON pu.id = d.unit_id
				WHERE d.receipt_id = :id
				ORDER BY d.id
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource("id", receiptId), APPROVE_DETAIL_ROW);
	}

	public record ApproveDetailRow(int productId, int unitId, int quantity, BigDecimal costPrice, String batchNumber,
			LocalDate expiryDate, BigDecimal conversionRate, boolean baseUnit) {
	}

	public record InventoryInsert(int productId, int locationId, String batchNumber, LocalDate expiryDate, int quantity) {
	}

	public record InventoryLogItem(int productId, int quantityChange, int unitId, Integer userId, long receiptId,
			Integer toLocationId, String referenceNote) {
	}

	public record InventoryLockRow(long id, int productId, String batchNumber) {
	}

	public List<Integer> findActiveProductIds(List<Integer> ids) {
		if (ids == null || ids.isEmpty()) {
			return List.of();
		}
		String sql = "SELECT id FROM products WHERE id IN (:ids) AND status = 'Active'";
		return namedJdbc.query(sql, new MapSqlParameterSource("ids", ids), (rs, i) -> rs.getInt("id"));
	}

	public List<UnitRow> findUnitsByTuples(List<int[]> tuples) {
		if (tuples == null || tuples.isEmpty()) {
			return List.of();
		}
		Integer[] ids = tuples.stream().map(t -> t[0]).toArray(Integer[]::new);
		Integer[] productIds = tuples.stream().map(t -> t[1]).toArray(Integer[]::new);
		String sql = """
				SELECT id, product_id, is_base_unit, conversion_rate
				FROM productunits
				WHERE (id, product_id) IN (
				  SELECT * FROM unnest(:ids, :productIds) AS t(id, product_id)
				)
				""";
		return namedJdbc.query(sql, Map.of("ids", ids, "productIds", productIds), UNIT_ROW);
	}

	public void batchInsertDetails(long receiptId, List<StockReceiptDetailRequest> details) {
		if (details == null || details.isEmpty()) {
			return;
		}
		String sql = """
				INSERT INTO stockreceiptdetails (receipt_id, product_id, unit_id, quantity, cost_price, batch_number, expiry_date)
				VALUES (:receipt_id, :product_id, :unit_id, :quantity, :cost_price, :batch_number, :expiry_date)
				""";
		MapSqlParameterSource[] batch = new MapSqlParameterSource[details.size()];
		for (int i = 0; i < details.size(); i++) {
			StockReceiptDetailRequest d = details.get(i);
			LocalDate exp = null;
			if (d.expiryDate() != null && !d.expiryDate().isBlank()) {
				exp = LocalDate.parse(d.expiryDate());
			}
			batch[i] = new MapSqlParameterSource("receipt_id", receiptId)
					.addValue("product_id", d.productId())
					.addValue("unit_id", d.unitId())
					.addValue("quantity", d.quantity())
					.addValue("cost_price", d.costPrice())
					.addValue("batch_number", blankToNull(d.batchNumber()), Types.VARCHAR)
					.addValue("expiry_date", exp != null ? java.sql.Date.valueOf(exp) : null, Types.DATE);
		}
		namedJdbc.batchUpdate(sql, batch);
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

	public List<InventoryLockRow> findInventoryByProductsForUpdate(int locationId, List<Integer> productIds) {
		if (productIds == null || productIds.isEmpty()) {
			return List.of();
		}
		String sql = """
				SELECT id, product_id, batch_number
				FROM inventory
				WHERE location_id = :loc AND product_id IN (:pids)
				FOR UPDATE
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource("loc", locationId).addValue("pids", productIds),
				(rs, rn) -> new InventoryLockRow(rs.getLong("id"), rs.getInt("product_id"), rs.getString("batch_number")));
	}

	public void updateInventoryQuantitiesBatch(Map<Long, Integer> idToDelta) {
		if (idToDelta == null || idToDelta.isEmpty()) {
			return;
		}
		StringBuilder sb = new StringBuilder("UPDATE inventory SET quantity = quantity + CASE id ");
		var src = new MapSqlParameterSource();
		int i = 0;
		for (var entry : idToDelta.entrySet()) {
			String idParam = "id" + i;
			String valParam = "v" + i;
			sb.append("WHEN :").append(idParam).append(" THEN :").append(valParam).append(" ");
			src.addValue(idParam, entry.getKey());
			src.addValue(valParam, entry.getValue());
			i++;
		}
		sb.append("END, updated_at = CURRENT_TIMESTAMP WHERE id IN (:ids)");
		src.addValue("ids", new ArrayList<>(idToDelta.keySet()));
		namedJdbc.update(sb.toString(), src);
	}

	public void batchInsertInventory(List<InventoryInsert> items) {
		if (items == null || items.isEmpty()) {
			return;
		}
		String sql = """
				INSERT INTO inventory (product_id, location_id, batch_number, expiry_date, quantity, min_quantity)
				VALUES (:pid, :loc, :batch, :exp, :qty, 0)
				""";
		MapSqlParameterSource[] batch = new MapSqlParameterSource[items.size()];
		for (int i = 0; i < items.size(); i++) {
			InventoryInsert it = items.get(i);
			batch[i] = new MapSqlParameterSource("pid", it.productId())
					.addValue("loc", it.locationId())
					.addValue("batch", it.batchNumber(), Types.VARCHAR)
					.addValue("exp", it.expiryDate() != null ? java.sql.Date.valueOf(it.expiryDate()) : null, Types.DATE)
					.addValue("qty", it.quantity());
		}
		namedJdbc.batchUpdate(sql, batch);
	}

	public void batchInsertInventoryLogs(List<InventoryLogItem> items) {
		if (items == null || items.isEmpty()) {
			return;
		}
		String sql = """
				INSERT INTO inventorylogs (product_id, action_type, quantity_change, unit_id, user_id, dispatch_id, receipt_id, from_location_id, to_location_id, reference_note)
				VALUES (:pid, 'INBOUND', :qchg, :uid_unit, :user_id, NULL, :receipt_id, NULL, :to_loc, :note)
				""";
		MapSqlParameterSource[] batch = new MapSqlParameterSource[items.size()];
		for (int i = 0; i < items.size(); i++) {
			InventoryLogItem it = items.get(i);
			batch[i] = new MapSqlParameterSource("pid", it.productId())
					.addValue("qchg", it.quantityChange())
					.addValue("uid_unit", it.unitId())
					.addValue("user_id", it.userId(), Types.INTEGER)
					.addValue("receipt_id", it.receiptId())
					.addValue("to_loc", it.toLocationId())
					.addValue("note", it.referenceNote(), Types.VARCHAR);
		}
		namedJdbc.batchUpdate(sql, batch);
	}

	private static String blankToNull(String s) {
		if (s == null || s.isBlank()) {
			return null;
		}
		return s.trim();
	}

	public Optional<Long> findInventoryIdForUpdate(int productId, int locationId, String batchNumber) {
		String sql = """
				SELECT i.id FROM inventory i
				WHERE i.product_id = :pid AND i.location_id = :loc
				  AND i.batch_number IS NOT DISTINCT FROM CAST(:batch AS varchar)
				FOR UPDATE
				""";
		List<Long> ids = namedJdbc.query(sql,
				new MapSqlParameterSource("pid", productId).addValue("loc", locationId).addValue("batch", batchNumber,
						Types.VARCHAR),
				(rs, row) -> rs.getLong("id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public void updateInventoryQuantity(long inventoryId, int deltaQty) {
		namedJdbc.update("UPDATE inventory SET quantity = quantity + :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("d", deltaQty).addValue("id", inventoryId));
	}

	public long insertInventory(int productId, int locationId, String batchNumber, LocalDate expiryDate, int quantity) {
		String sql = """
				INSERT INTO inventory (product_id, location_id, batch_number, expiry_date, quantity, min_quantity)
				VALUES (:pid, :loc, :batch, :exp, :qty, 0)
				RETURNING id
				""";
		Long id = namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("pid", productId).addValue("loc", locationId)
						.addValue("batch", batchNumber, Types.VARCHAR)
						.addValue("exp", expiryDate != null ? java.sql.Date.valueOf(expiryDate) : null, Types.DATE)
						.addValue("qty", quantity),
				Long.class);
		if (id == null) {
			throw new IllegalStateException("INSERT inventory không trả id");
		}
		return id;
	}

	public void insertInventoryLog(int productId, int quantityChange, int baseUnitId, Integer userId, long receiptId,
			Integer toLocationId, String referenceNote) {
		String sql = """
				INSERT INTO inventorylogs (product_id, action_type, quantity_change, unit_id, user_id, dispatch_id, receipt_id, from_location_id, to_location_id, reference_note)
				VALUES (:pid, 'INBOUND', :qchg, :uid_unit, :user_id, NULL, :receipt_id, NULL, :to_loc, :note)
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("pid", productId).addValue("qchg", quantityChange).addValue("uid_unit", baseUnitId)
						.addValue("user_id", userId, Types.INTEGER).addValue("receipt_id", receiptId)
						.addValue("to_loc", toLocationId).addValue("note", referenceNote, Types.VARCHAR));
	}

	public Optional<StockReceiptViewData> loadView(long receiptId) {
		String hsql = """
				SELECT
				  sr.id, sr.receipt_code, sr.supplier_id, s.name AS supplier_name, sr.staff_id, u_staff.full_name AS staff_name,
				  sr.receipt_date, sr.status, sr.invoice_number, sr.total_amount, sr.notes,
				  sr.approved_by, u_appr.full_name AS approved_by_name, sr.approved_at,
				  sr.reviewed_by, u_rev.full_name AS reviewed_by_name, sr.reviewed_at,
				  sr.rejection_reason, sr.created_at, sr.updated_at
				FROM stockreceipts sr
				INNER JOIN suppliers s ON s.id = sr.supplier_id
				INNER JOIN users u_staff ON u_staff.id = sr.staff_id
				LEFT JOIN users u_appr ON u_appr.id = sr.approved_by
				LEFT JOIN users u_rev ON u_rev.id = sr.reviewed_by
				WHERE sr.id = :id
				""";
		List<HeaderSnapshot> headers = namedJdbc.query(hsql, new MapSqlParameterSource("id", receiptId), HEADER_SNAPSHOT);
		if (headers.isEmpty()) {
			return Optional.empty();
		}
		HeaderSnapshot h = headers.getFirst();
		String dsql = """
				SELECT d.id, d.receipt_id, d.product_id, p.name AS product_name, p.sku_code, d.unit_id, pu.unit_name,
				  d.quantity, d.cost_price, d.batch_number, d.expiry_date, d.line_total
				FROM stockreceiptdetails d
				INNER JOIN products p ON p.id = d.product_id
				INNER JOIN productunits pu ON pu.id = d.unit_id
				WHERE d.receipt_id = :id
				ORDER BY d.id
				""";
		List<StockReceiptLineViewData> lines = namedJdbc.query(dsql, new MapSqlParameterSource("id", receiptId), VIEW_LINE);
		return Optional.of(h.toView(lines));
	}

	public List<StockReceiptLineViewData> loadDetailLines(long receiptId) {
		String dsql = """
				SELECT d.id, d.receipt_id, d.product_id, p.name AS product_name, p.sku_code, d.unit_id, pu.unit_name,
				  d.quantity, d.cost_price, d.batch_number, d.expiry_date, d.line_total
				FROM stockreceiptdetails d
				INNER JOIN products p ON p.id = d.product_id
				INNER JOIN productunits pu ON pu.id = d.unit_id
				WHERE d.receipt_id = :id
				ORDER BY d.id
				""";
		return namedJdbc.query(dsql, new MapSqlParameterSource("id", receiptId), VIEW_LINE);
	}

	public record NamePair(String supplierName, String staffName) {
	}

	public NamePair loadNames(int supplierId, int staffId) {
		String sql = "SELECT (SELECT name FROM suppliers WHERE id = :supplierId) AS supplier_name, (SELECT full_name FROM users WHERE id = :staffId) AS staff_name";
		return namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("supplierId", supplierId).addValue("staffId", staffId),
				(rs, i) -> new NamePair(rs.getString("supplier_name"), rs.getString("staff_name")));
	}

	public record HeaderSnapshot(long id, String receiptCode, long supplierId, String supplierName, int staffId,
			String staffName, LocalDate receiptDate, String status, String invoiceNumber, BigDecimal totalAmount, String notes,
			Integer approvedBy, String approvedByName, Instant approvedAt, Integer reviewedBy, String reviewedByName,
			Instant reviewedAt, String rejectionReason, Instant createdAt, Instant updatedAt) {
		StockReceiptViewData toView(List<StockReceiptLineViewData> details) {
			return new StockReceiptViewData(id, receiptCode, supplierId, supplierName, staffId, staffName, receiptDate, status,
					invoiceNumber, totalAmount, notes, approvedBy, approvedByName, approvedAt, reviewedBy, reviewedByName,
					reviewedAt, rejectionReason, createdAt, updatedAt, details);
		}
	}

	public StockReceiptViewData buildView(HeaderSnapshot header, List<StockReceiptLineViewData> lines) {
		return header.toView(lines);
	}

	public Optional<HeaderSnapshot> loadHeaderSnapshot(long receiptId) {
		String sql = """
				SELECT
				  sr.id, sr.receipt_code, sr.supplier_id, s.name AS supplier_name, sr.staff_id, u_staff.full_name AS staff_name,
				  sr.receipt_date, sr.status, sr.invoice_number, sr.total_amount, sr.notes,
				  sr.approved_by, u_appr.full_name AS approved_by_name, sr.approved_at,
				  sr.reviewed_by, u_rev.full_name AS reviewed_by_name, sr.reviewed_at,
				  sr.rejection_reason, sr.created_at, sr.updated_at
				FROM stockreceipts sr
				INNER JOIN suppliers s ON s.id = sr.supplier_id
				INNER JOIN users u_staff ON u_staff.id = sr.staff_id
				LEFT JOIN users u_appr ON u_appr.id = sr.approved_by
				LEFT JOIN users u_rev ON u_rev.id = sr.reviewed_by
				WHERE sr.id = :id
				""";
		var list = namedJdbc.query(sql, new MapSqlParameterSource("id", receiptId), HEADER_SNAPSHOT);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	private static final RowMapper<ReceiptHeaderLockRow> HEADER_LOCK_ROW = (rs, i) -> new ReceiptHeaderLockRow(rs.getLong("id"),
			rs.getString("receipt_code"), rs.getLong("supplier_id"), rs.getInt("staff_id"),
			rs.getObject("receipt_date", LocalDate.class), rs.getString("status"), rs.getString("invoice_number"),
			rs.getBigDecimal("total_amount"), rs.getString("notes"));

	private static final RowMapper<UnitRow> UNIT_ROW = (rs, i) -> new UnitRow(rs.getInt("id"), rs.getInt("product_id"),
			rs.getBoolean("is_base_unit"), rs.getBigDecimal("conversion_rate"));

	private static final RowMapper<ApproveDetailRow> APPROVE_DETAIL_ROW = (rs, i) -> new ApproveDetailRow(rs.getInt("product_id"),
			rs.getInt("unit_id"), rs.getInt("quantity"), rs.getBigDecimal("cost_price"), rs.getString("batch_number"),
			rs.getObject("expiry_date", LocalDate.class), rs.getBigDecimal("conversion_rate"), rs.getBoolean("is_base_unit"));

	private static final RowMapper<HeaderSnapshot> HEADER_SNAPSHOT = (rs, i) -> new HeaderSnapshot(rs.getLong("id"),
			rs.getString("receipt_code"), rs.getLong("supplier_id"), rs.getString("supplier_name"), rs.getInt("staff_id"),
			rs.getString("staff_name"), rs.getObject("receipt_date", LocalDate.class), rs.getString("status"),
			rs.getString("invoice_number"), rs.getBigDecimal("total_amount"), rs.getString("notes"),
			(Integer) rs.getObject("approved_by", Integer.class), rs.getString("approved_by_name"),
			toInstant(rs.getTimestamp("approved_at")), (Integer) rs.getObject("reviewed_by", Integer.class),
			rs.getString("reviewed_by_name"), toInstant(rs.getTimestamp("reviewed_at")), rs.getString("rejection_reason"),
			toInstantNonNull(rs.getTimestamp("created_at")), toInstantNonNull(rs.getTimestamp("updated_at")));

	private static final RowMapper<StockReceiptLineViewData> VIEW_LINE = (rs, i) -> new StockReceiptLineViewData(rs.getLong("id"),
			rs.getLong("receipt_id"), rs.getInt("product_id"), rs.getString("product_name"), rs.getString("sku_code"),
			rs.getInt("unit_id"), rs.getString("unit_name"), rs.getInt("quantity"), rs.getBigDecimal("cost_price"),
			rs.getString("batch_number"), rs.getObject("expiry_date", LocalDate.class), rs.getBigDecimal("line_total"));

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : null;
	}

	private static Instant toInstantNonNull(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}
}
