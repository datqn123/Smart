package com.example.smart_erp.custominterface.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

@Repository
public class CustomInterfaceJdbcRepository {

	private final JdbcTemplate jdbcTemplate;

	public CustomInterfaceJdbcRepository(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
	}

	public List<FolderRow> findActiveFolders() {
		return jdbcTemplate.query("""
				SELECT id, folder_key, label, icon, description, status, sort_order, visibility_roles,
				       draft_version, published_version, etag, updated_at, published_at
				FROM custom_menu_folders
				WHERE archived_at IS NULL
				ORDER BY sort_order ASC, id ASC
				""", folderMapper());
	}

	public List<PageRow> findActivePages() {
		return jdbcTemplate.query("""
				SELECT id, page_key, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
				       status, sort_order, visibility_roles, entity_permission, data_permission,
				       draft_version, published_version, etag, updated_at, published_at
				FROM custom_menu_pages
				WHERE archived_at IS NULL
				ORDER BY parent_folder_key ASC, sort_order ASC, id ASC
				""", pageMapper());
	}

	public Optional<FolderRow> findFolder(String key) {
		List<FolderRow> rows = jdbcTemplate.query("""
				SELECT id, folder_key, label, icon, description, status, sort_order, visibility_roles,
				       draft_version, published_version, etag, updated_at, published_at
				FROM custom_menu_folders
				WHERE folder_key = ? AND archived_at IS NULL
				""", folderMapper(), key);
		return rows.stream().findFirst();
	}

	public Optional<PageRow> findPage(String key) {
		List<PageRow> rows = jdbcTemplate.query("""
				SELECT id, page_key, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
				       status, sort_order, visibility_roles, entity_permission, data_permission,
				       draft_version, published_version, etag, updated_at, published_at
				FROM custom_menu_pages
				WHERE page_key = ? AND archived_at IS NULL
				""", pageMapper(), key);
		return rows.stream().findFirst();
	}

	public Optional<PageRow> findPublishedPage(String key) {
		List<PageRow> rows = jdbcTemplate.query("""
				SELECT id, page_key, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
				       status, sort_order, visibility_roles, entity_permission, data_permission,
				       draft_version, published_version, etag, updated_at, published_at
				FROM custom_menu_pages
				WHERE page_key = ? AND status = 'Published' AND archived_at IS NULL
				""", pageMapper(), key);
		return rows.stream().findFirst();
	}

	public boolean folderKeyExists(String key, Long exceptId) {
		Integer count = exceptId == null
				? jdbcTemplate.queryForObject("""
						SELECT COUNT(*) FROM custom_menu_folders
						WHERE folder_key = ? AND archived_at IS NULL
						""", Integer.class, key)
				: jdbcTemplate.queryForObject("""
						SELECT COUNT(*) FROM custom_menu_folders
						WHERE folder_key = ? AND archived_at IS NULL AND id <> ?
						""", Integer.class, key, exceptId);
		return count != null && count > 0;
	}

	public boolean pageKeyExists(String key, Long exceptId) {
		Integer count = exceptId == null
				? jdbcTemplate.queryForObject("""
						SELECT COUNT(*) FROM custom_menu_pages
						WHERE page_key = ? AND archived_at IS NULL
						""", Integer.class, key)
				: jdbcTemplate.queryForObject("""
						SELECT COUNT(*) FROM custom_menu_pages
						WHERE page_key = ? AND archived_at IS NULL AND id <> ?
						""", Integer.class, key, exceptId);
		return count != null && count > 0;
	}

	public boolean routeExists(String routePath, Long exceptId) {
		Integer count = exceptId == null
				? jdbcTemplate.queryForObject("""
						SELECT COUNT(*) FROM custom_menu_pages
						WHERE route_path = ? AND archived_at IS NULL
						""", Integer.class, routePath)
				: jdbcTemplate.queryForObject("""
						SELECT COUNT(*) FROM custom_menu_pages
						WHERE route_path = ? AND archived_at IS NULL AND id <> ?
						""", Integer.class, routePath, exceptId);
		return count != null && count > 0;
	}

	public FolderRow insertFolder(String key, String label, String icon, String description, String rolesJson,
			int sortOrder, int userId) {
		KeyHolder keyHolder = new GeneratedKeyHolder();
		jdbcTemplate.update(con -> {
			var ps = con.prepareStatement("""
					INSERT INTO custom_menu_folders (
						folder_key, label, icon, description, status, sort_order, visibility_roles,
						draft_version, etag, created_by, updated_by
					)
					VALUES (?, ?, ?, ?, 'Draft', ?, ?::jsonb, 1, ?, ?, ?)
					""", new String[] { "id" });
			ps.setString(1, key);
			ps.setString(2, label);
			ps.setString(3, icon);
			ps.setString(4, description);
			ps.setInt(5, sortOrder);
			ps.setString(6, rolesJson);
			ps.setString(7, folderEtag(key, 1));
			ps.setInt(8, userId);
			ps.setInt(9, userId);
			return ps;
		}, keyHolder);
		Number id = keyHolder.getKey();
		return findFolder(key).orElseThrow(() -> new IllegalStateException("Inserted folder missing: " + id));
	}

	public FolderRow updateFolder(FolderRow current, String key, String label, String icon, String description,
			String rolesJson, int sortOrder, int userId) {
		int nextVersion = current.draftVersion() + 1;
		jdbcTemplate.update("""
				UPDATE custom_menu_folders
				SET folder_key = ?, label = ?, icon = ?, description = ?, sort_order = ?,
				    visibility_roles = ?::jsonb, draft_version = ?, etag = ?, updated_by = ?, updated_at = now()
				WHERE id = ?
				""", key, label, icon, description, sortOrder, rolesJson, nextVersion, folderEtag(key, nextVersion),
				userId, current.id());
		if (!current.key().equals(key)) {
			jdbcTemplate.update("""
					UPDATE custom_menu_pages
					SET parent_folder_key = ?, updated_by = ?, updated_at = now()
					WHERE parent_folder_key = ? AND archived_at IS NULL
					""", key, userId, current.key());
		}
		return findFolder(key).orElseThrow();
	}

	public PageRow insertPage(String parentKey, String key, String label, String icon, String description,
			String routePath, String entityKey, String pageType, String rolesJson, String entityPermission,
			String dataPermission, int sortOrder, int userId) {
		jdbcTemplate.update("""
				INSERT INTO custom_menu_pages (
					page_key, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
					status, sort_order, visibility_roles, entity_permission, data_permission,
					draft_version, etag, created_by, updated_by
				)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NeedsConfig', ?, ?::jsonb, ?, ?, 1, ?, ?, ?)
				""", key, parentKey, label, icon, description, routePath, entityKey, pageType, sortOrder, rolesJson,
				entityPermission, dataPermission, pageEtag(key, 1), userId, userId);
		return findPage(key).orElseThrow();
	}

	public PageRow updatePage(PageRow current, String parentKey, String key, String label, String icon,
			String description, String routePath, String entityKey, String pageType, String rolesJson,
			String entityPermission, String dataPermission, int sortOrder, int userId) {
		int nextVersion = current.draftVersion() + 1;
		jdbcTemplate.update("""
				UPDATE custom_menu_pages
				SET page_key = ?, parent_folder_key = ?, label = ?, icon = ?, description = ?,
				    route_path = ?, entity_key = ?, page_type = ?, sort_order = ?, visibility_roles = ?::jsonb,
				    entity_permission = ?, data_permission = ?, draft_version = ?, etag = ?,
				    updated_by = ?, updated_at = now()
				WHERE id = ?
				""", key, parentKey, label, icon, description, routePath, entityKey, pageType, sortOrder, rolesJson,
				entityPermission, dataPermission, nextVersion, pageEtag(key, nextVersion), userId, current.id());
		return findPage(key).orElseThrow();
	}

	public void updateFolderOrder(String key, int sortOrder, int userId) {
		jdbcTemplate.update("""
				UPDATE custom_menu_folders
				SET sort_order = ?, draft_version = draft_version + 1,
				    etag = 'folder-' || folder_key || '-draft-' || (draft_version + 1),
				    updated_by = ?, updated_at = now()
				WHERE folder_key = ? AND archived_at IS NULL
				""", sortOrder, userId, key);
	}

	public void updatePageOrder(String key, int sortOrder, int userId) {
		jdbcTemplate.update("""
				UPDATE custom_menu_pages
				SET sort_order = ?, draft_version = draft_version + 1,
				    etag = 'page-' || page_key || '-draft-' || (draft_version + 1),
				    updated_by = ?, updated_at = now()
				WHERE page_key = ? AND archived_at IS NULL
				""", sortOrder, userId, key);
	}

	public PageRow bumpPageDraft(PageRow current, int userId) {
		int nextVersion = current.draftVersion() + 1;
		int updated = jdbcTemplate.update("""
				UPDATE custom_menu_pages
				SET draft_version = ?, etag = ?, updated_by = ?, updated_at = now()
				WHERE page_key = ? AND draft_version = ? AND etag = ? AND archived_at IS NULL
				""", nextVersion, pageEtag(current.key(), nextVersion), userId, current.key(),
				current.draftVersion(), current.etag());
		if (updated != 1) {
			throw new OptimisticLockingFailureException("Stale custom menu page draft: " + current.key());
		}
		return findPage(current.key()).orElseThrow();
	}

	public void publishAll(int userId) {
		jdbcTemplate.update("""
				UPDATE custom_menu_folders
				SET status = 'Published', published_version = draft_version, published_at = now(),
				    updated_by = ?, updated_at = now()
				WHERE archived_at IS NULL
				""", userId);
		jdbcTemplate.update("""
				UPDATE custom_menu_pages
				SET status = 'Published', published_version = draft_version, published_at = now(),
				    updated_by = ?, updated_at = now()
				WHERE archived_at IS NULL
				""", userId);
		jdbcTemplate.update("""
				INSERT INTO custom_menu_folder_versions (
					folder_key, version, label, icon, description, sort_order, visibility_roles, published_by
				)
				SELECT folder_key, draft_version, label, icon, description, sort_order, visibility_roles, ?
				FROM custom_menu_folders
				WHERE archived_at IS NULL
				ON CONFLICT (folder_key, version) DO NOTHING
				""", userId);
		jdbcTemplate.update("""
				INSERT INTO custom_menu_page_versions (
					page_key, version, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
					sort_order, visibility_roles, entity_permission, data_permission, published_by
				)
				SELECT page_key, draft_version, parent_folder_key, label, icon, description, route_path, entity_key,
				       page_type, sort_order, visibility_roles, entity_permission, data_permission, ?
				FROM custom_menu_pages
				WHERE archived_at IS NULL
				ON CONFLICT (page_key, version) DO NOTHING
				""", userId);
	}

	public void publishPage(PageRow page, int userId) {
		int updated = jdbcTemplate.update("""
				UPDATE custom_menu_pages
				SET status = 'Published', published_version = ?, published_at = now(),
				    updated_by = ?, updated_at = now()
				WHERE page_key = ? AND draft_version = ? AND etag = ? AND archived_at IS NULL
				""", page.draftVersion(), userId, page.key(), page.draftVersion(), page.etag());
		if (updated != 1) {
			throw new OptimisticLockingFailureException("Stale custom menu page publish: " + page.key());
		}
		jdbcTemplate.update("""
				INSERT INTO custom_menu_page_versions (
					page_key, version, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
					sort_order, visibility_roles, entity_permission, data_permission, published_by
				)
				SELECT page_key, draft_version, parent_folder_key, label, icon, description, route_path, entity_key,
				       page_type, sort_order, visibility_roles, entity_permission, data_permission, ?
				FROM custom_menu_pages
				WHERE page_key = ? AND draft_version = ? AND etag = ? AND archived_at IS NULL
				ON CONFLICT (page_key, version) DO NOTHING
				""", userId, page.key(), page.draftVersion(), page.etag());
	}

	public int countPublishedPagesInFolder(String folderKey) {
		Integer count = jdbcTemplate.queryForObject("""
				SELECT COUNT(*) FROM custom_menu_pages
				WHERE parent_folder_key = ? AND status = 'Published' AND archived_at IS NULL
				""", Integer.class, folderKey);
		return count == null ? 0 : count;
	}

	public void archiveFolder(String key, int userId) {
		jdbcTemplate.update("""
				UPDATE custom_menu_folders
				SET status = 'Hidden', archived_at = now(), updated_by = ?, updated_at = now()
				WHERE folder_key = ? AND archived_at IS NULL
				""", userId, key);
	}

	public void archivePage(String key, int userId) {
		jdbcTemplate.update("""
				UPDATE custom_menu_pages
				SET status = 'Hidden', archived_at = now(), updated_by = ?, updated_at = now()
				WHERE page_key = ? AND archived_at IS NULL
				""", userId, key);
	}

	public void event(String targetType, String targetKey, String eventType, int userId) {
		jdbcTemplate.update("""
				INSERT INTO custom_menu_events(target_type, target_key, event_type, created_by)
				VALUES (?, ?, ?, ?)
				""", targetType, targetKey, eventType, userId);
	}

	public static String folderEtag(String key, int version) {
		return "folder-" + key + "-draft-" + version;
	}

	public static String pageEtag(String key, int version) {
		return "page-" + key + "-draft-" + version;
	}

	private static RowMapper<FolderRow> folderMapper() {
		return (rs, rowNum) -> new FolderRow(
				rs.getLong("id"),
				rs.getString("folder_key"),
				rs.getString("label"),
				rs.getString("icon"),
				rs.getString("description"),
				rs.getString("status"),
				rs.getInt("sort_order"),
				rs.getString("visibility_roles"),
				rs.getInt("draft_version"),
				nullableInt(rs, "published_version"),
				rs.getString("etag"),
				instant(rs, "updated_at"),
				instant(rs, "published_at"));
	}

	private static RowMapper<PageRow> pageMapper() {
		return (rs, rowNum) -> new PageRow(
				rs.getLong("id"),
				rs.getString("page_key"),
				rs.getString("parent_folder_key"),
				rs.getString("label"),
				rs.getString("icon"),
				rs.getString("description"),
				rs.getString("route_path"),
				rs.getString("entity_key"),
				rs.getString("page_type"),
				rs.getString("status"),
				rs.getInt("sort_order"),
				rs.getString("visibility_roles"),
				rs.getString("entity_permission"),
				rs.getString("data_permission"),
				rs.getInt("draft_version"),
				nullableInt(rs, "published_version"),
				rs.getString("etag"),
				instant(rs, "updated_at"),
				instant(rs, "published_at"));
	}

	private static Integer nullableInt(ResultSet rs, String column) throws SQLException {
		int value = rs.getInt(column);
		return rs.wasNull() ? null : value;
	}

	private static Instant instant(ResultSet rs, String column) throws SQLException {
		var ts = rs.getTimestamp(column);
		return ts == null ? null : ts.toInstant();
	}

	public record FolderRow(long id, String key, String label, String icon, String description, String status,
			int sortOrder, String rolesJson, int draftVersion, Integer publishedVersion, String etag,
			Instant updatedAt, Instant publishedAt) {
	}

	public record PageRow(long id, String key, String parentKey, String label, String icon, String description,
			String routePath, String entityKey, String pageType, String status, int sortOrder, String rolesJson,
			String entityPermission, String dataPermission, int draftVersion, Integer publishedVersion,
			String etag, Instant updatedAt, Instant publishedAt) {
	}
}
