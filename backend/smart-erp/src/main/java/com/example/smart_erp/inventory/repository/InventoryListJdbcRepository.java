package com.example.smart_erp.inventory.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.inventory.query.InventoryListQuery;
import com.example.smart_erp.inventory.query.InventoryStockLevel;
import com.example.smart_erp.inventory.response.InventorySummaryData;

/**
 * Đọc tồn theo SRS Task005; SQL dialect PostgreSQL (bảng Flyway V1).
 */
@SuppressWarnings("null")
@Repository
public class InventoryListJdbcRepository {

	private static final String BASE_FROM = """
			FROM inventory i
			INNER JOIN products p ON p.id = i.product_id
			INNER JOIN warehouselocations wl ON wl.id = i.location_id
			INNER JOIN productunits pub ON pub.product_id = p.id AND pub.is_base_unit = true
			LEFT JOIN productunits pud ON pud.id = i.unit_id
			LEFT JOIN LATERAL (
			  SELECT pph1.cost_price AS latest_cost
			  FROM productpricehistory pph1
			  WHERE pph1.product_id = p.id AND pph1.unit_id = COALESCE(i.unit_id, pub.id)
			  ORDER BY pph1.effective_date DESC, pph1.id DESC
			  LIMIT 1
			) pph ON true
			""";

	private static final String SELECT_LIST_COLUMNS = """
			SELECT
			  i.id,
			  i.product_id,
			  p.name AS product_name,
			  p.sku_code,
			  p.barcode,
			  i.location_id,
			  wl.warehouse_code,
			  wl.shelf_code,
			  i.batch_number,
			  i.expiry_date,
			  i.quantity,
			  i.min_quantity,
			  COALESCE(pud.id, pub.id) AS unit_id,
			  COALESCE(pud.unit_name, pub.unit_name) AS unit_name,
			  pph.latest_cost,
			  i.updated_at
			""";

	private final NamedParameterJdbcTemplate namedJdbc;

	public InventoryListJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public InventorySummaryData loadSummary(InventoryListQuery q) {
		Filter f = buildFilter(q);
		String sql = """
				SELECT
				  COUNT(*)::bigint AS total_skus,
				  COALESCE(SUM(i.quantity::numeric * COALESCE(pph.latest_cost::numeric, 0)), 0) AS total_value,
				  COALESCE(SUM(
				    CASE
				      WHEN i.quantity > 0 AND i.quantity <= i.min_quantity
				      THEN 1
				      ELSE 0
				    END
				  ), 0)::bigint AS low_stock_count,
				  COALESCE(SUM(
				    CASE
				      WHEN i.expiry_date IS NOT NULL
				        AND i.expiry_date <= (CURRENT_DATE + interval '30 day')
				        AND i.quantity > 0
				      THEN 1
				      ELSE 0
				    END
				  ), 0)::bigint AS expiring_soon_count
				""" + BASE_FROM + f.where;
		return namedJdbc.queryForObject(sql, f.source, (rs, n) -> new InventorySummaryData(
				rs.getLong("total_skus"),
				rs.getBigDecimal("total_value"),
				rs.getLong("low_stock_count"),
				rs.getLong("expiring_soon_count")));
	}

	public long countRows(InventoryListQuery q) {
		Filter f = buildFilter(q);
		String sql = "SELECT COUNT(*) " + BASE_FROM + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	/**
	 * Task 2 — gộp summary + count: chạy 1 query duy nhất, trả về cả KPI và tổng
	 * số dòng. Tận dụng cùng {@link #BASE_FROM} + filter; vẫn giữ {@link #loadSummary}
	 * và {@link #countRows} cho {@code summary()} và các caller khác.
	 *
	 * <p>Lưu ý: {@code total_skus} và {@code total_rows} đều dùng {@code COUNT(*)} over
	 * cùng {@code BASE_FROM + filter}, nên luôn bằng nhau. Tên field {@code total_skus}
	 * giữ theo semantic API cũ (tương đương {@code loadSummary().totalSkus()}); giá trị
	 * thực tế là <b>số dòng inventory trong filter</b>, không phải số SKU distinct.
	 * Nếu sau này cần đếm distinct product, thêm field mới thay vì đổi field này
	 * (để tránh breaking change).
	 */
	public InventorySummaryWithCount loadSummaryWithCount(InventoryListQuery q) {
		Filter f = buildFilter(q);
		String sql = """
				SELECT
				  COUNT(*)::bigint AS total_rows,
				  -- total_skus: cùng COUNT(*) over filter; giữ tên theo API cũ
				  COUNT(*)::bigint AS total_skus,
				  COALESCE(SUM(i.quantity::numeric * COALESCE(pph.latest_cost::numeric, 0)), 0) AS total_value,
				  COALESCE(SUM(
				    CASE
				      WHEN i.quantity > 0 AND i.quantity <= i.min_quantity
				      THEN 1
				      ELSE 0
				    END
				  ), 0)::bigint AS low_stock_count,
				  COALESCE(SUM(
				    CASE
				      WHEN i.expiry_date IS NOT NULL
				        AND i.expiry_date <= (CURRENT_DATE + interval '30 day')
				        AND i.quantity > 0
				      THEN 1
				      ELSE 0
				    END
				  ), 0)::bigint AS expiring_soon_count
				""" + BASE_FROM + f.where;
		return namedJdbc.queryForObject(sql, f.source, (rs, n) -> {
			long total = rs.getLong("total_rows");
			InventorySummaryData summary = new InventorySummaryData(
					rs.getLong("total_skus"),
					rs.getBigDecimal("total_value"),
					rs.getLong("low_stock_count"),
					rs.getLong("expiring_soon_count"));
			return new InventorySummaryWithCount(summary, total);
		});
	}

	public record InventorySummaryWithCount(InventorySummaryData summary, long total) {
	}

	public List<InventoryListRow> loadPage(InventoryListQuery q) {
		Filter f = buildFilter(q);
		int offset = (q.page() - 1) * q.limit();
		String sql = SELECT_LIST_COLUMNS + BASE_FROM + f.where + " ORDER BY i.id ASC LIMIT :_lim OFFSET :_off";
		f.source.addValue("_lim", q.limit());
		f.source.addValue("_off", offset);
		return namedJdbc.query(sql, f.source, ROW);
	}

	/** Task006 — một dòng tồn (cùng cột với list). */
	public Optional<InventoryListRow> findById(long id) {
		String sql = SELECT_LIST_COLUMNS + BASE_FROM + " WHERE i.id = :_id";
		var src = new MapSqlParameterSource("_id", id);
		List<InventoryListRow> list = namedJdbc.query(sql, src, ROW);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.get(0));
	}

	private static final String SELECT_RELATED = """
			SELECT
			  i2.id,
			  i2.batch_number,
			  i2.quantity,
			  i2.expiry_date,
			  wl2.warehouse_code,
			  wl2.shelf_code
			FROM inventory i2
			INNER JOIN warehouselocations wl2 ON wl2.id = i2.location_id
			WHERE i2.product_id = :_product_id
			  AND i2.id <> :_exclude_id
			  AND i2.quantity > 0
			ORDER BY i2.id ASC
			""";

	/** Task006 — các lô cùng SP, khác id, chỉ còn hàng (SRS OQ-2). */
	public List<InventoryRelatedLineRow> findRelatedLines(long productId, long excludeInventoryId) {
		var src = new MapSqlParameterSource("_product_id", productId).addValue("_exclude_id", excludeInventoryId);
		return namedJdbc.query(SELECT_RELATED, src, RELATED_ROW);
	}

	private static final RowMapper<InventoryRelatedLineRow> RELATED_ROW = InventoryListJdbcRepository::mapRelatedRow;

	private static InventoryRelatedLineRow mapRelatedRow(ResultSet rs, int i) throws SQLException {
		var q = rs.getBigDecimal("quantity");
		int qn = q != null ? q.intValue() : 0;
		return new InventoryRelatedLineRow(
				rs.getLong("id"),
				rs.getString("batch_number"),
				qn,
				rs.getObject("expiry_date", LocalDate.class),
				rs.getString("warehouse_code"),
				rs.getString("shelf_code"));
	}

	public record InventoryRelatedLineRow(
			long id,
			String batchNumber,
			int quantity,
			LocalDate expiryDate,
			String warehouseCode,
			String shelfCode) {
	}

	private static final RowMapper<InventoryListRow> ROW = InventoryListJdbcRepository::mapListRow;

	private static InventoryListRow mapListRow(ResultSet rs, int i) throws SQLException {
		Instant upd = rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toInstant() : Instant.parse("1970-01-01T00:00:00Z");
		var cost = rs.getBigDecimal("latest_cost");
		return new InventoryListRow(
				rs.getLong("id"),
				rs.getLong("product_id"),
				rs.getString("product_name"),
				rs.getString("sku_code"),
				rs.getString("barcode"),
				rs.getInt("location_id"),
				rs.getString("warehouse_code"),
				rs.getString("shelf_code"),
				rs.getString("batch_number"),
				rs.getObject("expiry_date", LocalDate.class),
				rs.getInt("quantity"),
				rs.getInt("min_quantity"),
				rs.getInt("unit_id"),
				rs.getString("unit_name"),
				cost == null ? java.math.BigDecimal.ZERO : cost,
				upd);
	}

	public record InventoryListRow(
			long id,
			long productId,
			String productName,
			String skuCode,
			String barcode,
			int locationId,
			String warehouseCode,
			String shelfCode,
			String batchNumber,
			LocalDate expiryDate,
			int quantity,
			int minQuantity,
			int unitId,
			String unitName,
			java.math.BigDecimal costPrice,
			Instant updatedAt) {
	}

	private Filter buildFilter(InventoryListQuery q) {
		StringBuilder sb = new StringBuilder(" WHERE 1=1");
		var src = new MapSqlParameterSource();
		appendStockLevel(q.stockLevel(), sb);
		if (q.search() != null) {
			sb.append(" AND (p.name ilike :_search OR p.sku_code ilike :_search)");
			src.addValue("_search", buildSearchPattern(q.search()));
		}
		if (q.locationId() != null) {
			sb.append(" AND i.location_id = :_location_id");
			src.addValue("_location_id", q.locationId());
		}
		if (q.categoryId() != null) {
			sb.append(" AND p.category_id = :_category_id");
			src.addValue("_category_id", q.categoryId());
		}
		if (q.productId() != null) {
			sb.append(" AND i.product_id = :_product_id");
			src.addValue("_product_id", q.productId());
		}
		return new Filter(sb.toString(), src);
	}

	private static void appendStockLevel(InventoryStockLevel s, StringBuilder sb) {
		if (s == null || s == InventoryStockLevel.ALL) {
			return;
		}
		if (s == InventoryStockLevel.IN_STOCK) {
			sb.append(" AND i.quantity > i.min_quantity");
		}
		else if (s == InventoryStockLevel.LOW_STOCK) {
			sb.append(" AND i.quantity > 0 AND i.quantity <= i.min_quantity");
		}
		else if (s == InventoryStockLevel.OUT_OF_STOCK) {
			sb.append(" AND i.quantity = 0");
		}
	}

	/**
	 * Loại ký tự joker thường gặp trong tìm theo tên, tránh tác động ILIKE; param vẫn
	 * gắn theo tên nên an toàn SQLi.
	 */
	public static String buildSearchPattern(String raw) {
		String t = raw.trim();
		if (t.isEmpty()) {
			return "%";
		}
		t = t.replace("%", "").replace("_", "");
		if (t.isEmpty()) {
			return "%";
		}
		return "%" + t + "%";
	}

	private static final class Filter {
		/** Cùng tệp: outer cần đọc. */
		final String where;
		/** Cùng tệp. */
		final MapSqlParameterSource source;

		Filter(String w, MapSqlParameterSource s) {
			this.where = w;
			this.source = s;
		}
	}
}
