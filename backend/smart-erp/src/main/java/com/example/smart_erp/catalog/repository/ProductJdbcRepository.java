package com.example.smart_erp.catalog.repository;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.sql.Date;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.catalog.response.ProductGalleryImageData;
import com.example.smart_erp.catalog.response.ProductListItemData;
import com.example.smart_erp.catalog.response.ProductUnitRow;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@SuppressWarnings("null")
@Repository
public class ProductJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public ProductJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public long countList(String search, Integer categoryId, String status) {
		StringBuilder sql = new StringBuilder("""
				SELECT COUNT(*)::bigint FROM products p
				JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
				WHERE 1 = 1
				""");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(sql, p, search, categoryId, status);
		Long n = namedJdbc.queryForObject(sql.toString(), p, Long.class);
		return n == null ? 0L : n;
	}

	public List<ProductListItemData> findListPage(String search, Integer categoryId, String status, String orderBySql,
			int limit, int offset) {
		StringBuilder sql = new StringBuilder("""
				SELECT p.id, p.sku_code, p.barcode, p.name, p.category_id, c.name AS category_name, p.image_url, p.status,
				       COALESCE(inv.qty, 0)::bigint AS current_stock,
				       latest_pph.sale_price AS current_price,
				       p.created_at, p.updated_at
				FROM products p
				JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
				LEFT JOIN categories c ON c.id = p.category_id
				LEFT JOIN (
				  SELECT product_id, SUM(quantity)::bigint AS qty FROM inventory GROUP BY product_id
				) inv ON inv.product_id = p.id
				LEFT JOIN LATERAL (
				  SELECT pph.sale_price
				  FROM productpricehistory pph
				  WHERE pph.product_id = p.id AND pph.unit_id = pu.id AND pph.effective_date <= CURRENT_DATE
				  ORDER BY pph.effective_date DESC, pph.id DESC
				  LIMIT 1
				) latest_pph ON TRUE
				WHERE 1 = 1
				""");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(sql, p, search, categoryId, status);
		sql.append(" ORDER BY ").append(orderBySql).append(" LIMIT :lim OFFSET :off");
		p.addValue("lim", limit).addValue("off", offset);
		return namedJdbc.query(sql.toString(), p, LIST_ITEM_MAPPER);
	}

	private static void appendListFilters(StringBuilder sql, MapSqlParameterSource p, String search,
			Integer categoryId, String status) {
		if (search != null && !search.isBlank()) {
			sql.append(" AND (p.name ILIKE :s OR p.sku_code ILIKE :s OR p.barcode ILIKE :s)");
			p.addValue("s", "%" + search.trim() + "%");
		}
		if (categoryId != null) {
			sql.append(" AND p.category_id = :cid");
			p.addValue("cid", categoryId);
		}
		if (status != null && !status.isBlank() && !"all".equalsIgnoreCase(status)) {
			sql.append(" AND p.status = :st");
			p.addValue("st", status);
		}
	}

	private static final RowMapper<ProductListItemData> LIST_ITEM_MAPPER = (rs, rn) -> mapListItem(rs);

	private static ProductListItemData mapListItem(ResultSet rs) throws SQLException {
		Integer categoryId = (Integer) rs.getObject("category_id");
		BigDecimal price = rs.getBigDecimal("current_price");
		return new ProductListItemData(rs.getInt("id"), rs.getString("sku_code"), rs.getString("barcode"),
				rs.getString("name"), categoryId, rs.getString("category_name"), rs.getString("image_url"),
				rs.getString("status"), rs.getLong("current_stock"), price, toInstant(rs.getTimestamp("created_at")),
				toInstant(rs.getTimestamp("updated_at")));
	}

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	public static String resolveListOrderBy(String sortRaw) {
		String s = sortRaw == null || sortRaw.isBlank() ? "id:asc" : sortRaw.trim();
		return switch (s) {
			case "id:asc" -> "p.id ASC";
			case "id:desc" -> "p.id DESC";
			case "name:asc" -> "p.name ASC, p.id ASC";
			case "name:desc" -> "p.name DESC, p.id ASC";
			case "skuCode:asc" -> "p.sku_code ASC, p.id ASC";
			case "skuCode:desc" -> "p.sku_code DESC, p.id ASC";
			case "updatedAt:asc" -> "p.updated_at ASC, p.id ASC";
			case "updatedAt:desc" -> "p.updated_at DESC, p.id ASC";
			case "createdAt:asc" -> "p.created_at ASC, p.id ASC";
			case "createdAt:desc" -> "p.created_at DESC, p.id ASC";
			default -> throw new IllegalArgumentException("sort");
		};
	}

	public boolean existsSku(String skuCode) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM products WHERE sku_code = :s LIMIT 1",
				Map.of("s", skuCode), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public Optional<Integer> findIdBySku(String skuCode) {
		List<Integer> hit = namedJdbc.query("SELECT id FROM products WHERE sku_code = :s LIMIT 1",
				Map.of("s", skuCode), (rs, rn) -> rs.getInt("id"));
		return hit.isEmpty() ? Optional.empty() : Optional.of(hit.getFirst());
	}

	public boolean existsOtherSku(int excludeId, String skuCode) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM products WHERE sku_code = :s AND id <> :id LIMIT 1",
				Map.of("s", skuCode, "id", excludeId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int insertProduct(Integer categoryId, String skuCode, String barcode, String name, String description,
			BigDecimal weight, String status, String imageUrl) {
		KeyHolder kh = new GeneratedKeyHolder();
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("category_id", categoryId);
		p.addValue("sku_code", skuCode);
		p.addValue("barcode", barcode);
		p.addValue("name", name);
		p.addValue("description", description);
		p.addValue("weight", weight);
		p.addValue("status", status);
		p.addValue("image_url", imageUrl);
		namedJdbc.update("""
				INSERT INTO products (category_id, sku_code, barcode, name, description, weight, status, image_url)
				VALUES (:category_id, :sku_code, :barcode, :name, :description, :weight, :status, :image_url)
				""", p, kh, new String[] { "id" });
		Number key = kh.getKey();
		if (key == null) {
			throw new IllegalStateException("INSERT products did not return id");
		}
		return key.intValue();
	}

	public int insertBaseUnit(int productId, String unitName) {
		KeyHolder kh = new GeneratedKeyHolder();
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("pid", productId);
		p.addValue("uname", unitName);
		namedJdbc.update("""
				INSERT INTO productunits (product_id, unit_name, conversion_rate, is_base_unit)
				VALUES (:pid, :uname, 1, TRUE)
				""", p, kh, new String[] { "id" });
		Number key = kh.getKey();
		if (key == null) {
			throw new IllegalStateException("INSERT productunits did not return id");
		}
		return key.intValue();
	}

	public void insertPriceHistory(int productId, int unitId, BigDecimal costPrice, BigDecimal salePrice,
			LocalDate effectiveDate) {
		namedJdbc.update("""
				INSERT INTO productpricehistory (product_id, unit_id, cost_price, sale_price, effective_date)
				VALUES (:pid, :uid, :cost, :sale, :eff)
				""", new MapSqlParameterSource("pid", productId).addValue("uid", unitId).addValue("cost", costPrice)
				.addValue("sale", salePrice).addValue("eff", Date.valueOf(effectiveDate)));
	}

	public Optional<ProductListItemData> findListItemById(int productId) {
		String sql = """
				SELECT p.id, p.sku_code, p.barcode, p.name, p.category_id, c.name AS category_name, p.image_url, p.status,
				       COALESCE(inv.qty, 0)::bigint AS current_stock,
				       latest_pph.sale_price AS current_price,
				       p.created_at, p.updated_at
				FROM products p
				JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
				LEFT JOIN categories c ON c.id = p.category_id
				LEFT JOIN (
				  SELECT product_id, SUM(quantity)::bigint AS qty FROM inventory GROUP BY product_id
				) inv ON inv.product_id = p.id
				LEFT JOIN LATERAL (
				  SELECT pph.sale_price
				  FROM productpricehistory pph
				  WHERE pph.product_id = p.id AND pph.unit_id = pu.id AND pph.effective_date <= CURRENT_DATE
				  ORDER BY pph.effective_date DESC, pph.id DESC
				  LIMIT 1
				) latest_pph ON TRUE
				WHERE p.id = :id
				""";
		List<ProductListItemData> rows = namedJdbc.query(sql, Map.of("id", productId), LIST_ITEM_MAPPER);
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public void lockProductsForUpdate(List<Integer> ids) {
		lockProductsForUpdateBatch(ids);
	}

	/**
	 * Khóa nhiều products trong 1 query bằng {@code SELECT ... FOR UPDATE} kèm {@code ORDER BY id} để tránh
	 * deadlock giữa các tiến trình đồng thời. Dùng thay cho vòng lặp per-row nhằm giảm N+1.
	 *
	 * <p>Trả về danh sách {@link ProductLockSnapshot} thực sự bị khóa; nếu số row trả về &lt; số id đầu vào,
	 * tức là có id bị xóa mất giữa lúc check existence và lúc lock (TOCTOU) — phương thức sẽ ném
	 * {@link BusinessException} với {@link ApiErrorCode#CONFLICT} để client nhận lỗi rõ ràng.
	 *
	 * @param ids danh sách id cần khóa; nếu rỗng trả về list rỗng
	 * @return danh sách snapshot của các sản phẩm đã khóa
	 * @throws BusinessException nếu một trong các id không tồn tại khi lock (TOCTOU)
	 */
	public List<ProductLockSnapshot> lockProductsForUpdateBatch(List<Integer> ids) {
		if (ids == null || ids.isEmpty()) {
			return Collections.emptyList();
		}
		String sql = """
				SELECT p.id, p.sku_code, p.barcode, p.name, p.category_id, p.description, p.weight, p.status, p.image_url
				FROM products p WHERE p.id IN (:ids) ORDER BY p.id FOR UPDATE
				""";
		Integer[] idArray = ids.toArray(new Integer[0]);
		List<ProductLockSnapshot> rows = namedJdbc.query(sql, Map.of("ids", idArray), (rs, rn) -> {
			Integer categoryId = (Integer) rs.getObject("category_id");
			BigDecimal w = (BigDecimal) rs.getObject("weight");
			return new ProductLockSnapshot(rs.getInt("id"), rs.getString("sku_code"), rs.getString("barcode"),
					rs.getString("name"), categoryId, rs.getString("description"), w, rs.getString("status"),
					rs.getString("image_url"));
		});
		if (rows.size() < idArray.length) {
			Set<Integer> lockedIds = new HashSet<>();
			for (ProductLockSnapshot s : rows) {
				lockedIds.add(s.id());
			}
			for (Integer id : ids) {
				if (!lockedIds.contains(id)) {
					throw new BusinessException(ApiErrorCode.CONFLICT, "Sản phẩm đã bị xóa bởi người dùng khác",
							Map.of("id", id.toString()));
				}
			}
		}
		return rows;
	}

	public Optional<ProductLockSnapshot> lockProductForUpdate(int productId) {
		String sql = """
				SELECT p.id, p.sku_code, p.barcode, p.name, p.category_id, p.description, p.weight, p.status, p.image_url
				FROM products p WHERE p.id = :id FOR UPDATE
				""";
		List<ProductLockSnapshot> rows = namedJdbc.query(sql, Map.of("id", productId), (rs, rn) -> {
			Integer categoryId = (Integer) rs.getObject("category_id");
			BigDecimal w = (BigDecimal) rs.getObject("weight");
			return new ProductLockSnapshot(rs.getInt("id"), rs.getString("sku_code"), rs.getString("barcode"),
					rs.getString("name"), categoryId, rs.getString("description"), w, rs.getString("status"),
					rs.getString("image_url"));
		});
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public void updateProduct(int id, String skuCode, String barcode, String name, Integer categoryId,
			String description, BigDecimal weight, String status, String imageUrl) {
		namedJdbc.update("""
				UPDATE products SET
				  sku_code = :sku_code,
				  barcode = :barcode,
				  name = :name,
				  category_id = :category_id,
				  description = :description,
				  weight = :weight,
				  status = :status,
				  image_url = :image_url,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""", new MapSqlParameterSource("id", id).addValue("sku_code", skuCode).addValue("barcode", barcode)
				.addValue("name", name).addValue("category_id", categoryId).addValue("description", description)
				.addValue("weight", weight).addValue("status", status).addValue("image_url", imageUrl));
	}

	public Optional<Integer> findBaseUnitId(int productId) {
		List<Integer> ids = namedJdbc.query(
				"SELECT id FROM productunits WHERE product_id = :pid AND is_base_unit = TRUE LIMIT 1",
				Map.of("pid", productId), (rs, rn) -> rs.getInt("id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public Optional<BigDecimal[]> findLatestEffectivePrices(int productId, int unitId) {
		String sql = """
				SELECT cost_price, sale_price FROM productpricehistory
				WHERE product_id = :pid AND unit_id = :uid AND effective_date <= CURRENT_DATE
				ORDER BY effective_date DESC, id DESC LIMIT 1
				""";
		List<BigDecimal[]> rows = namedJdbc.query(sql, Map.of("pid", productId, "uid", unitId), (rs, rn) -> new BigDecimal[] {
				rs.getBigDecimal("cost_price"), rs.getBigDecimal("sale_price") });
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public long sumInventoryQuantity(int productId) {
		Long n = namedJdbc.queryForObject(
				"SELECT COALESCE(SUM(quantity), 0)::bigint FROM inventory WHERE product_id = :pid",
				Map.of("pid", productId), Long.class);
		return n == null ? 0L : n;
	}

	public boolean existsStockReceiptDetail(int productId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM stockreceiptdetails WHERE product_id = :pid LIMIT 1",
				Map.of("pid", productId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public boolean existsOrderDetail(int productId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM orderdetails WHERE product_id = :pid LIMIT 1",
				Map.of("pid", productId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int deleteProduct(int productId) {
		return namedJdbc.update("DELETE FROM products WHERE id = :id", Map.of("id", productId));
	}

	public int deleteProducts(List<Integer> ids) {
		if (ids.isEmpty()) {
			return 0;
		}
		return namedJdbc.update("DELETE FROM products WHERE id IN (:ids)", Map.of("ids", ids));
	}

	public boolean existsProductId(int productId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM products WHERE id = :id LIMIT 1", Map.of("id", productId),
				(rs, rn) -> 1);
		return !hit.isEmpty();
	}

	/**
	 * Trả về tập các id tồn tại trong bảng {@code products} (1 query batch). Tránh N+1 khi validate bulk request.
	 *
	 * @param ids danh sách id cần kiểm tra; nếu rỗng trả về tập rỗng
	 * @return tập id thực sự tồn tại trong DB
	 */
	public Set<Integer> findExistingProductIds(List<Integer> ids) {
		if (ids == null || ids.isEmpty()) {
			return Collections.emptySet();
		}
		List<Integer> rows = namedJdbc.query("SELECT id FROM products WHERE id IN (:ids)",
				Map.of("ids", ids), (rs, rn) -> rs.getInt("id"));
		return new HashSet<>(rows);
	}

	/**
	 * Trả về map id -> lý do block (chỉ chứa id bị block) cho bulk delete. Dùng {@code unnest(:ids)} + LATERAL
	 * join để gom 3N truy vấn (stock receipt, order detail, inventory sum) về 1 query duy nhất.
	 *
	 * <p>Lý do block ưu tiên theo thứ tự: {@code HAS_STOCK_RECEIPT} > {@code HAS_ORDER_LINES} > {@code HAS_STOCK}
	 * (giữ nguyên thứ tự của {@link #sumInventoryQuantity}/{@link #existsStockReceiptDetail}/{@link #existsOrderDetail}).
	 *
	 * @param ids danh sách id cần kiểm tra; nếu rỗng trả về map rỗng
	 * @return map chỉ chứa id bị block, giá trị là mã lý do ({@code HAS_STOCK_RECEIPT} / {@code HAS_ORDER_LINES} /
	 *         {@code HAS_STOCK})
	 */
	public Map<Integer, String> findBulkDeleteBlockReasons(List<Integer> ids) {
		if (ids == null || ids.isEmpty()) {
			return Collections.emptyMap();
		}
		String sql = """
				SELECT p.id,
				  CASE
				    WHEN EXISTS (SELECT 1 FROM stockreceiptdetails WHERE product_id = p.id)
				      THEN 'HAS_STOCK_RECEIPT'
				    WHEN EXISTS (SELECT 1 FROM orderdetails WHERE product_id = p.id)
				      THEN 'HAS_ORDER_LINES'
				    WHEN COALESCE(inv.qty, 0) > 0
				      THEN 'HAS_STOCK'
				    ELSE NULL
				  END AS block_reason
				FROM unnest(:ids) AS p(id)
				LEFT JOIN LATERAL (
				  SELECT SUM(quantity) AS qty FROM inventory WHERE product_id = p.id
				) inv ON true
				""";
		// NamedParameterJdbcTemplate yêu cầu mảng (không phải List) cho unnest(:ids)
		Integer[] idArray = ids.toArray(new Integer[0]);
		List<BlockedRow> rows = namedJdbc.query(sql, Map.of("ids", idArray), (rs, rn) -> {
			int id = rs.getInt("id");
			String reason = rs.getString("block_reason");
			return new BlockedRow(id, reason);
		});
		Map<Integer, String> result = new HashMap<>();
		for (BlockedRow r : rows) {
			if (r.reason() != null) {
				result.put(r.id(), r.reason());
			}
		}
		return result;
	}

	private record BlockedRow(int id, String reason) {
	}

	public Optional<ProductDetailHeaderRow> loadDetailHeader(int productId) {
		String sql = """
				SELECT p.id, p.sku_code, p.barcode, p.name, p.category_id, c.name AS category_name,
				       p.description, p.weight, p.status, p.image_url, p.created_at, p.updated_at
				FROM products p
				LEFT JOIN categories c ON c.id = p.category_id
				WHERE p.id = :id
				""";
		List<ProductDetailHeaderRow> rows = namedJdbc.query(sql, Map.of("id", productId), (rs, rn) -> {
			Integer categoryId = (Integer) rs.getObject("category_id");
			BigDecimal w = (BigDecimal) rs.getObject("weight");
			return new ProductDetailHeaderRow(rs.getInt("id"), rs.getString("sku_code"), rs.getString("barcode"),
					rs.getString("name"), categoryId, rs.getString("category_name"), rs.getString("description"), w,
					rs.getString("status"), rs.getString("image_url"), toInstant(rs.getTimestamp("created_at")),
					toInstant(rs.getTimestamp("updated_at")));
		});
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	/** Giá vốn hiện hành theo đơn vị (bảng giá), null nếu không có bản ghi. */
	public Optional<BigDecimal> findCurrentCostPrice(int productId, int unitId) {
		String sql = """
				SELECT (
				  SELECT ph.cost_price FROM productpricehistory ph
				  WHERE ph.product_id = :pid AND ph.unit_id = :uid AND ph.effective_date <= CURRENT_DATE
				  ORDER BY ph.effective_date DESC, ph.id DESC LIMIT 1
				) AS cur_cost
				""";
		return namedJdbc.query(sql, Map.of("pid", productId, "uid", unitId), rs -> {
			if (!rs.next()) {
				return Optional.empty();
			}
			return Optional.ofNullable(rs.getBigDecimal("cur_cost"));
		});
	}

	public List<ProductUnitRow> listUnitsWithCurrentPrices(int productId) {
		String sql = """
				SELECT u.id, u.unit_name, u.conversion_rate, u.is_base_unit,
				  (SELECT cost_price FROM productpricehistory ph
				   WHERE ph.product_id = u.product_id AND ph.unit_id = u.id AND ph.effective_date <= CURRENT_DATE
				   ORDER BY ph.effective_date DESC, ph.id DESC LIMIT 1) AS cur_cost,
				  (SELECT sale_price FROM productpricehistory ph2
				   WHERE ph2.product_id = u.product_id AND ph2.unit_id = u.id AND ph2.effective_date <= CURRENT_DATE
				   ORDER BY ph2.effective_date DESC, ph2.id DESC LIMIT 1) AS cur_sale
				FROM productunits u
				WHERE u.product_id = :pid
				ORDER BY u.is_base_unit DESC, u.id
				""";
		return namedJdbc.query(sql, Map.of("pid", productId), (rs, rn) -> {
			BigDecimal cr = rs.getBigDecimal("conversion_rate");
			return new ProductUnitRow(rs.getInt("id"), rs.getString("unit_name"), cr, rs.getBoolean("is_base_unit"),
					rs.getBigDecimal("cur_cost"), rs.getBigDecimal("cur_sale"));
		});
	}

	public List<ProductGalleryImageData> listGalleryImages(int productId) {
		return namedJdbc.query("""
				SELECT id, image_url, sort_order, is_primary FROM productimages
				WHERE product_id = :pid ORDER BY sort_order, id
				""", Map.of("pid", productId), (rs, rn) -> new ProductGalleryImageData(rs.getInt("id"),
				rs.getString("image_url"), rs.getInt("sort_order"), rs.getBoolean("is_primary")));
	}

	public record ProductLockSnapshot(int id, String skuCode, String barcode, String name, Integer categoryId,
			String description, BigDecimal weight, String status, String imageUrl) {
	}

	public record ProductDetailHeaderRow(int id, String skuCode, String barcode, String name, Integer categoryId,
			String categoryName, String description, BigDecimal weight, String status, String imageUrl,
			Instant createdAt, Instant updatedAt) {
	}
}
