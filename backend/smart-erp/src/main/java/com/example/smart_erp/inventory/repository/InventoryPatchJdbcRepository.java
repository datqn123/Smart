package com.example.smart_erp.inventory.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Types;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

/**
 * Ghi và khóa dòng tồn — SRS Task007 (PATCH meta).
 */
@SuppressWarnings("null")
@Repository
public class InventoryPatchJdbcRepository {

	private static final RowMapper<InventoryLockRow> LOCK_ROW = InventoryPatchJdbcRepository::mapLockRow;

	private final NamedParameterJdbcTemplate namedJdbc;

	public InventoryPatchJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public Optional<InventoryLockRow> lockInventoryRow(long id) {
		String sql = """
				SELECT
				  i.id,
				  i.product_id,
				  p.sku_code AS sku_code,
				  i.location_id,
				  i.batch_number,
				  i.expiry_date,
				  i.min_quantity,
				  i.quantity,
				  i.unit_id,
				  p.status AS product_status,
				  wl.status AS location_status
				FROM inventory i
				JOIN products p ON p.id = i.product_id
				JOIN warehouselocations wl ON wl.id = i.location_id
				WHERE i.id = :_id
				FOR UPDATE OF i
				""";
		var src = new MapSqlParameterSource("_id", id);
		List<InventoryLockRow> rows = namedJdbc.query(sql, src, LOCK_ROW);
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.get(0));
	}

	public Optional<String> findWarehouseLocationStatus(int locationId) {
		String sql = "SELECT status FROM warehouselocations WHERE id = :_id";
		var src = new MapSqlParameterSource("_id", locationId);
		List<String> list = namedJdbc.query(sql, src, (rs, n) -> rs.getString("status"));
		return list.isEmpty() ? Optional.empty() : Optional.of(list.get(0));
	}

	public boolean productUnitBelongsToProduct(int unitId, int productId) {
		String sql = "SELECT COUNT(*)::int FROM productunits WHERE id = :_uid AND product_id = :_pid";
		var src = new MapSqlParameterSource("_uid", unitId).addValue("_pid", productId);
		Integer c = namedJdbc.queryForObject(sql, src, Integer.class);
		return c != null && c > 0;
	}

	public int countDuplicateOtherLine(int productId, int locationId, String batchKey, long excludeInventoryId) {
		String sql = """
				SELECT COUNT(*)::int
				FROM inventory
				WHERE product_id = :_product_id
				  AND location_id = :_location_id
				  AND batch_number IS NOT DISTINCT FROM :_batch_key
				  AND id <> :_exclude_id
				""";
		var src = new MapSqlParameterSource("_product_id", productId)
				.addValue("_location_id", locationId)
				.addValue("_batch_key", batchKey, Types.VARCHAR)
				.addValue("_exclude_id", excludeInventoryId);
		Integer c = namedJdbc.queryForObject(sql, src, Integer.class);
		return c != null ? c : 0;
	}

	public void updateInventory(long inventoryId, boolean setLocation, Integer locationId, boolean setMinQuantity,
			Integer minQuantity, boolean setBatch, String batchNumberOrNull, boolean setExpiry, LocalDate expiryOrNull,
			boolean setUnit, Integer unitIdOrNull) {
		var parts = new ArrayList<String>();
		var src = new MapSqlParameterSource("_id", inventoryId);
		if (setLocation) {
			parts.add("location_id = :_location_id");
			src.addValue("_location_id", locationId);
		}
		if (setMinQuantity) {
			parts.add("min_quantity = :_min_quantity");
			src.addValue("_min_quantity", minQuantity);
		}
		if (setBatch) {
			parts.add("batch_number = :_batch_number");
			src.addValue("_batch_number", batchNumberOrNull, Types.VARCHAR);
		}
		if (setExpiry) {
			parts.add("expiry_date = :_expiry_date");
			src.addValue("_expiry_date", expiryOrNull, Types.DATE);
		}
		if (setUnit) {
			parts.add("unit_id = :_unit_id");
			src.addValue("_unit_id", unitIdOrNull, Types.INTEGER);
		}
		if (parts.isEmpty()) {
			return;
		}
		parts.add("updated_at = CURRENT_TIMESTAMP");
		String sql = "UPDATE inventory SET " + String.join(", ", parts) + " WHERE id = :_id";
		namedJdbc.update(sql, src);
	}

	public List<Integer> findActiveOwnerUserIds() {
		String sql = """
				SELECT u.id
				FROM users u
				INNER JOIN roles r ON r.id = u.role_id
				WHERE r.name = 'Owner' AND u.status = 'Active'
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource(), (rs, n) -> rs.getInt("id"));
	}

	public void insertNotificationForOwner(int ownerUserId, String title, String message, int inventoryId) {
		String sql = """
				INSERT INTO notifications (user_id, notification_type, title, message, is_read, reference_type, reference_id)
				VALUES (:_user_id, 'SystemAlert', :_title, :_message, FALSE, 'Inventory', :_ref_id)
				""";
		var src = new MapSqlParameterSource("_user_id", ownerUserId)
				.addValue("_title", title)
				.addValue("_message", message)
				.addValue("_ref_id", inventoryId);
		namedJdbc.update(sql, src);
	}

	public void insertNotificationsForOwners(String title, String message, int refId, int excludeUserId) {
		String sql = """
				INSERT INTO notifications (user_id, notification_type, title, message, is_read, reference_type, reference_id)
				SELECT u.id, 'SystemAlert', :_title, :_message, FALSE, 'Inventory', :_ref_id
				FROM users u
				INNER JOIN roles r ON r.id = u.role_id
				WHERE r.name = 'Owner' AND u.status = 'Active' AND u.id <> :_exclude_id
				""";
		var src = new MapSqlParameterSource("_title", title)
				.addValue("_message", message)
				.addValue("_ref_id", refId)
				.addValue("_exclude_id", excludeUserId);
		namedJdbc.update(sql, src);
	}

	private static InventoryLockRow mapLockRow(ResultSet rs, int i) throws SQLException {
		int uid = rs.getInt("unit_id");
		boolean wasNull = rs.wasNull();
		return new InventoryLockRow(
				rs.getLong("id"),
				rs.getInt("product_id"),
				rs.getString("sku_code"),
				rs.getInt("location_id"),
				rs.getString("batch_number"),
				rs.getObject("expiry_date", LocalDate.class),
				rs.getInt("min_quantity"),
				rs.getInt("quantity"),
				wasNull ? null : uid,
				rs.getString("product_status"),
				rs.getString("location_status"));
	}

	public record InventoryLockRow(
			long id,
			int productId,
			String skuCode,
			int locationId,
			String batchNumber,
			LocalDate expiryDate,
			int minQuantity,
			int quantity,
			Integer unitId,
			String productStatus,
			String locationStatus) {
	}
}
