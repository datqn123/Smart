package com.example.smart_erp.sales.stock;

import java.math.BigDecimal;
import java.sql.Date;
import java.sql.Types;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

@SuppressWarnings("null")
@Repository
public class RetailStockJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public RetailStockJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public Optional<Integer> findDefaultRetailLocationId() {
		String sql = "SELECT default_retail_location_id FROM storeprofiles ORDER BY id LIMIT 1";
		return namedJdbc.query(sql, Map.of(), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			Integer id = (Integer) rs.getObject(1, Integer.class);
			return Optional.ofNullable(id);
		});
	}

	public Optional<BigDecimal> findConversionRate(int productUnitId) {
		String sql = "SELECT conversion_rate FROM productunits WHERE id = :id";
		return namedJdbc.query(sql, Map.of("id", productUnitId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			BigDecimal cr = (BigDecimal) rs.getObject(1, BigDecimal.class);
			return Optional.ofNullable(cr);
		});
	}

	public Optional<Integer> findBaseUnitId(int productId) {
		String sql = "SELECT id FROM productunits WHERE product_id = :pid AND is_base_unit = TRUE LIMIT 1";
		return namedJdbc.query(sql, Map.of("pid", productId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			Integer id = (Integer) rs.getObject(1, Integer.class);
			return Optional.ofNullable(id);
		});
	}

	public List<InventoryBucketRow> lockInventoryBucketsFefo(int productId, int locationId) {
		String sql = """
				SELECT id, quantity, batch_number, expiry_date
				FROM inventory
				WHERE product_id = :pid AND location_id = :loc AND quantity > 0
				ORDER BY expiry_date NULLS LAST, id
				FOR UPDATE
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource("pid", productId).addValue("loc", locationId),
				(rs, rn) -> new InventoryBucketRow(rs.getLong("id"), rs.getInt("quantity"), rs.getString("batch_number"),
						rs.getObject("expiry_date", LocalDate.class)));
	}

	public void deductInventory(long inventoryId, int deductBaseQty) {
		namedJdbc.update(
				"UPDATE inventory SET quantity = quantity - :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("d", deductBaseQty).addValue("id", inventoryId));
	}

	public void addInventory(long inventoryId, int addBaseQty) {
		namedJdbc.update(
				"UPDATE inventory SET quantity = quantity + :d, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				new MapSqlParameterSource("d", addBaseQty).addValue("id", inventoryId));
	}

	public long insertStockDispatchTempCode(String tempCode, Integer orderId, int userId, LocalDate dispatchDate,
			String status, String notes) {
		KeyHolder kh = new GeneratedKeyHolder();
		String sql = """
				INSERT INTO stockdispatches (dispatch_code, order_id, user_id, dispatch_date, status, notes)
				VALUES (:code, :oid, :uid, :d, :st, :notes)
				""";
		MapSqlParameterSource p = new MapSqlParameterSource("code", tempCode)
				.addValue("oid", orderId, Types.INTEGER)
				.addValue("uid", userId).addValue("d", Date.valueOf(dispatchDate)).addValue("st", status)
				.addValue("notes", notes, Types.VARCHAR);
		namedJdbc.update(sql, p, kh, new String[] { "id" });
		Number key = kh.getKey();
		if (key == null) {
			throw new IllegalStateException("INSERT stockdispatches không trả id");
		}
		return key.longValue();
	}

	public void updateStockDispatchCode(long dispatchId, String dispatchCode) {
		namedJdbc.update("UPDATE stockdispatches SET dispatch_code = :c, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
				Map.of("c", dispatchCode, "id", dispatchId));
	}

	public void cancelDispatch(long dispatchId, String notesAppend) {
		String sql = """
				UPDATE stockdispatches
				SET status = 'Cancelled',
				    notes = CASE WHEN notes IS NULL OR notes = '' THEN :n ELSE notes || ' | ' || :n END,
				    updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("id", dispatchId).addValue("n", notesAppend, Types.VARCHAR));
	}

	public void insertInventoryLogOutbound(int productId, int deductBaseQty, int baseUnitId, int userId, long dispatchId,
			int fromLocationId, String referenceNote) {
		String sql = """
				INSERT INTO inventorylogs (
				  product_id, action_type, quantity_change, unit_id, user_id,
				  dispatch_id, receipt_id, from_location_id, to_location_id, reference_note
				) VALUES (
				  :pid, 'OUTBOUND', :qchg, :unit_id, :uid,
				  :did, NULL, :from_loc, NULL, :note
				)
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("pid", productId).addValue("qchg", -deductBaseQty)
				.addValue("unit_id", baseUnitId).addValue("uid", userId).addValue("did", dispatchId)
				.addValue("from_loc", fromLocationId).addValue("note", referenceNote, Types.VARCHAR));
	}

	public void insertInventoryLogInbound(int productId, int addBaseQty, int baseUnitId, int userId, long dispatchId,
			int toLocationId, String referenceNote) {
		String sql = """
				INSERT INTO inventorylogs (
				  product_id, action_type, quantity_change, unit_id, user_id,
				  dispatch_id, receipt_id, from_location_id, to_location_id, reference_note
				) VALUES (
				  :pid, 'INBOUND', :qchg, :unit_id, :uid,
				  :did, NULL, NULL, :to_loc, :note
				)
				""";
		namedJdbc.update(sql, new MapSqlParameterSource("pid", productId).addValue("qchg", addBaseQty)
				.addValue("unit_id", baseUnitId).addValue("uid", userId).addValue("did", dispatchId)
				.addValue("to_loc", toLocationId).addValue("note", referenceNote, Types.VARCHAR));
	}

	/** Tổng SL đơn vị cơ sở xuất theo sản phẩm (POS / log), dùng khi phiếu không có stockdispatch_lines. */
	public List<ProductOutboundBaseQtyRow> sumOutboundBaseQtyByProduct(long dispatchId) {
		String sql = """
				SELECT product_id, SUM(ABS(quantity_change))::int AS base_qty
				FROM inventorylogs
				WHERE dispatch_id = :did AND action_type = 'OUTBOUND'
				GROUP BY product_id
				ORDER BY product_id
				""";
		return namedJdbc.query(sql, Map.of("did", dispatchId), (rs, rn) -> new ProductOutboundBaseQtyRow(rs.getInt("product_id"),
				rs.getInt("base_qty")));
	}

	public List<OutboundLogRow> loadOutboundLogsByDispatch(long dispatchId) {
		String sql = """
				SELECT id, product_id, quantity_change, unit_id, from_location_id, reference_note
				FROM inventorylogs
				WHERE dispatch_id = :did AND action_type = 'OUTBOUND'
				ORDER BY id
				""";
		return namedJdbc.query(sql, Map.of("did", dispatchId), (rs, rn) -> new OutboundLogRow(rs.getLong("id"),
				rs.getInt("product_id"), rs.getInt("quantity_change"), rs.getInt("unit_id"),
				(Integer) rs.getObject("from_location_id"), rs.getString("reference_note")));
	}

	public List<Long> lockActiveDispatchIdsByOrder(int orderId) {
		String sql = """
				SELECT id FROM stockdispatches
				WHERE order_id = :oid AND status <> 'Cancelled'
				ORDER BY id
				FOR UPDATE
				""";
		return namedJdbc.query(sql, Map.of("oid", orderId), (rs, rn) -> rs.getLong("id"));
	}

	public void markOrderLinesDispatchedAll(int orderId) {
		namedJdbc.update("UPDATE orderdetails SET dispatched_qty = quantity WHERE order_id = :oid",
				Map.of("oid", orderId));
	}

	public void resetOrderLinesDispatched(int orderId) {
		namedJdbc.update("UPDATE orderdetails SET dispatched_qty = 0 WHERE order_id = :oid", Map.of("oid", orderId));
	}

	public record InventoryBucketRow(long inventoryId, int quantityBase, String batchNumber, LocalDate expiryDate) {
	}

	public record OutboundLogRow(long logId, int productId, int quantityChange, int unitId, Integer fromLocationId,
			String referenceNote) {
	}

	public record ProductOutboundBaseQtyRow(int productId, int baseQty) {
	}
}

