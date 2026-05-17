package com.example.smart_erp.catalog.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.catalog.response.CategoryBreadcrumbItemData;
import com.example.smart_erp.catalog.response.CategoryDetailData;
import com.example.smart_erp.catalog.response.CategoryNodeResponse;

@SuppressWarnings("null")
@Repository
public class CategoryJdbcRepository {

	private static final RowMapper<CategoryFlatRow> FLAT_ROW_MAPPER = (rs, rowNum) -> CategoryFlatRow.from(rs);

	private final NamedParameterJdbcTemplate namedJdbc;

	public CategoryJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public List<CategoryFlatRow> loadAllActive(String statusFilter) {
		StringBuilder sql = new StringBuilder("""
				SELECT c.id, c.category_code, c.name, c.description, c.parent_id, c.sort_order, c.status,
				       c.created_at, c.updated_at,
				       COALESCE(pc.cnt, 0)::bigint AS product_count
				FROM categories c
				LEFT JOIN (
				  SELECT category_id, COUNT(*)::bigint AS cnt FROM products GROUP BY category_id
				) pc ON pc.category_id = c.id
				WHERE c.deleted_at IS NULL
				""");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendStatus(sql, statusFilter);
		sql.append(" ORDER BY c.sort_order, c.name");
		return namedJdbc.query(sql.toString(), p, FLAT_ROW_MAPPER);
	}

	/** Exact name match (case-insensitive); empty if none or ambiguous. */
	public Optional<Long> findActiveIdByExactNameIgnoreCase(String name) {
		if (name == null || name.isBlank()) {
			return Optional.empty();
		}
		String sql = """
				SELECT id FROM categories
				WHERE deleted_at IS NULL AND status = 'Active'
				  AND LOWER(TRIM(name)) = LOWER(TRIM(:name))
				""";
		List<Long> ids = namedJdbc.query(sql, Map.of("name", name.trim()), (rs, rowNum) -> rs.getLong("id"));
		if (ids.size() == 1) {
			return Optional.of(ids.getFirst());
		}
		return Optional.empty();
	}

	/** Exact category_code match among active (non-deleted) rows. */
	public Optional<Long> findActiveIdByExactCode(String categoryCode) {
		if (categoryCode == null || categoryCode.isBlank()) {
			return Optional.empty();
		}
		String sql = """
				SELECT id FROM categories
				WHERE deleted_at IS NULL AND status = 'Active' AND category_code = :code
				""";
		List<Long> ids = namedJdbc.query(sql, Map.of("code", categoryCode.trim()), (rs, rowNum) -> rs.getLong("id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public boolean existsActiveWithNameIgnoreCase(String name) {
		return findActiveIdByExactNameIgnoreCase(name).isPresent();
	}

	public Optional<CategoryFlatRow> findActiveById(long id) {
		String sql = """
				SELECT c.id, c.category_code, c.name, c.description, c.parent_id, c.sort_order, c.status,
				       c.created_at, c.updated_at,
				       COALESCE(pc.cnt, 0)::bigint AS product_count
				FROM categories c
				LEFT JOIN (
				  SELECT category_id, COUNT(*)::bigint AS cnt FROM products GROUP BY category_id
				) pc ON pc.category_id = c.id
				WHERE c.id = :id AND c.deleted_at IS NULL
				""";
		List<CategoryFlatRow> rows = namedJdbc.query(sql, Map.of("id", id), FLAT_ROW_MAPPER);
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public Optional<CategoryFlatRow> lockActiveByIdForUpdate(long id) {
		String sql = """
				SELECT c.id, c.category_code, c.name, c.description, c.parent_id, c.sort_order, c.status,
				       c.created_at, c.updated_at,
				       COALESCE(pc.cnt, 0)::bigint AS product_count
				FROM categories c
				LEFT JOIN (
				  SELECT category_id, COUNT(*)::bigint AS cnt FROM products GROUP BY category_id
				) pc ON pc.category_id = c.id
				WHERE c.id = :id AND c.deleted_at IS NULL
				FOR UPDATE OF c
				""";
		List<CategoryFlatRow> rows = namedJdbc.query(sql, Map.of("id", id), FLAT_ROW_MAPPER);
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public boolean existsActiveId(long id) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM categories WHERE id = :id AND deleted_at IS NULL LIMIT 1",
				Map.of("id", id), (rs, rn) -> rs.getInt(1));
		return !hit.isEmpty();
	}

	/** Bất kỳ bản ghi categories (kể cả đã soft-delete). Dùng phân nhánh 404 vs 400 INVALID_CATEGORY khi gán SP. */
	public boolean existsCategoryRow(long id) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM categories WHERE id = :id LIMIT 1", Map.of("id", id),
				(rs, rn) -> rs.getInt(1));
		return !hit.isEmpty();
	}

	public boolean existsOtherActiveWithCode(long excludeId, String categoryCode) {
		List<Integer> hit = namedJdbc.query("""
				SELECT 1 FROM categories
				WHERE category_code = :code AND id <> :id AND deleted_at IS NULL
				LIMIT 1
				""", Map.of("code", categoryCode, "id", excludeId), (rs, rn) -> rs.getInt(1));
		return !hit.isEmpty();
	}

	public boolean existsActiveWithCode(String categoryCode) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM categories WHERE category_code = :code AND deleted_at IS NULL LIMIT 1",
				Map.of("code", categoryCode), (rs, rn) -> rs.getInt(1));
		return !hit.isEmpty();
	}

	public long countActiveChildren(long parentId) {
		Long n = namedJdbc.queryForObject(
				"SELECT COUNT(*)::bigint FROM categories WHERE parent_id = :pid AND deleted_at IS NULL",
				Map.of("pid", parentId), Long.class);
		return n == null ? 0L : n;
	}

	public long countProductsOnCategory(long categoryId) {
		Long n = namedJdbc.queryForObject("SELECT COUNT(*)::bigint FROM products WHERE category_id = :cid",
				Map.of("cid", categoryId), Long.class);
		return n == null ? 0L : n;
	}

	public Optional<String> findActiveName(long id) {
		List<String> names = namedJdbc.query(
				"SELECT name FROM categories WHERE id = :id AND deleted_at IS NULL LIMIT 1", Map.of("id", id),
				(rs, rn) -> rs.getString("name"));
		return names.isEmpty() ? Optional.empty() : Optional.ofNullable(names.getFirst());
	}

	public Optional<CategoryDetailData> loadDetail(long id) {
		Optional<CategoryFlatRow> row = findActiveById(id);
		if (row.isEmpty()) {
			return Optional.empty();
		}
		CategoryFlatRow c = row.get();
		String parentName = null;
		if (c.parentId() != null) {
			parentName = findActiveName(c.parentId()).orElse(null);
		}
		List<CategoryBreadcrumbItemData> trail = new ArrayList<>();
		Long cur = id;
		int guard = 0;
		while (cur != null && guard++ < 256) {
			Optional<CategoryFlatRow> step = findActiveById(cur);
			if (step.isEmpty()) {
				break;
			}
			CategoryFlatRow s = step.get();
			trail.addFirst(new CategoryBreadcrumbItemData(s.id(), s.name(), s.categoryCode()));
			cur = s.parentId();
		}
		return Optional.of(new CategoryDetailData(c.id(), c.categoryCode(), c.name(), c.description(), c.parentId(),
				parentName, c.sortOrder(), c.status(), c.productCount(), c.createdAt(), c.updatedAt(), trail));
	}

	public long insert(String categoryCode, String name, String description, Long parentId, int sortOrder,
			String status) {
		KeyHolder kh = new GeneratedKeyHolder();
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("category_code", categoryCode);
		p.addValue("name", name);
		p.addValue("description", description);
		p.addValue("parent_id", parentId);
		p.addValue("sort_order", sortOrder);
		p.addValue("status", status);
		namedJdbc.update("""
				INSERT INTO categories (category_code, name, description, parent_id, sort_order, status)
				VALUES (:category_code, :name, :description, :parent_id, :sort_order, :status)
				""", p, kh, new String[] { "id" });
		Number key = kh.getKey();
		if (key == null) {
			throw new IllegalStateException("INSERT categories không trả id");
		}
		return key.longValue();
	}

	public void update(long id, String categoryCode, String name, String description, Long parentId, Integer sortOrder,
			String status) {
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("id", id);
		p.addValue("category_code", categoryCode);
		p.addValue("name", name);
		p.addValue("description", description);
		p.addValue("parent_id", parentId);
		p.addValue("sort_order", sortOrder);
		p.addValue("status", status);
		namedJdbc.update("""
				UPDATE categories SET
				  category_code = :category_code,
				  name = :name,
				  description = :description,
				  parent_id = :parent_id,
				  sort_order = :sort_order,
				  status = :status,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id AND deleted_at IS NULL
				""", p);
	}

	public void softDelete(long id) {
		int n = namedJdbc.update(
				"UPDATE categories SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND deleted_at IS NULL",
				Map.of("id", id));
		if (n != 1) {
			throw new IllegalStateException("Soft-delete categories id=" + id + " không cập nhật đúng 1 dòng");
		}
	}

	public CategoryNodeResponse toNodeResponse(CategoryFlatRow c, List<CategoryNodeResponse> children) {
		return new CategoryNodeResponse(c.id(), c.categoryCode(), c.name(), c.description(), c.parentId(), c.sortOrder(),
				c.status(), c.productCount(), c.createdAt(), c.updatedAt(), children);
	}

	public CategoryNodeResponse toNodeResponseFlat(CategoryFlatRow c) {
		return new CategoryNodeResponse(c.id(), c.categoryCode(), c.name(), c.description(), c.parentId(), c.sortOrder(),
				c.status(), c.productCount(), c.createdAt(), c.updatedAt(), null);
	}

	public Map<Long, List<Long>> buildChildrenIndex(List<CategoryFlatRow> rows) {
		Map<Long, List<Long>> children = new HashMap<>();
		for (CategoryFlatRow r : rows) {
			if (r.parentId() != null) {
				children.computeIfAbsent(r.parentId(), k -> new ArrayList<>()).add(r.id());
			}
		}
		return children;
	}

	public List<CategoryParentEdgeRow> loadAllActiveParentEdges() {
		return namedJdbc.query(
				"SELECT id, parent_id FROM categories WHERE deleted_at IS NULL ORDER BY id",
				Map.of(), (rs, rn) -> {
					long id = rs.getLong("id");
					long pid = rs.getLong("parent_id");
					Long parentId = rs.wasNull() ? null : pid;
					return new CategoryParentEdgeRow(id, parentId);
				});
	}

	private static void appendStatus(StringBuilder sql, String statusFilter) {
		if ("Active".equalsIgnoreCase(statusFilter)) {
			sql.append(" AND c.status = 'Active'");
		}
		else if ("Inactive".equalsIgnoreCase(statusFilter)) {
			sql.append(" AND c.status = 'Inactive'");
		}
	}

	public record CategoryFlatRow(long id, String categoryCode, String name, String description, Long parentId,
			int sortOrder, String status, long productCount, Instant createdAt, Instant updatedAt) {

		static CategoryFlatRow from(ResultSet rs) throws SQLException {
			long parentIdRaw = rs.getLong("parent_id");
			Long parentId = rs.wasNull() ? null : parentIdRaw;
			return new CategoryFlatRow(rs.getLong("id"), rs.getString("category_code"), rs.getString("name"),
					rs.getString("description"), parentId, rs.getInt("sort_order"), rs.getString("status"),
					rs.getLong("product_count"), toInstantNonNull(rs.getTimestamp("created_at")),
					toInstantNonNull(rs.getTimestamp("updated_at")));
		}

		private static Instant toInstantNonNull(Timestamp ts) {
			return ts != null ? ts.toInstant() : Instant.EPOCH;
		}
	}
}
