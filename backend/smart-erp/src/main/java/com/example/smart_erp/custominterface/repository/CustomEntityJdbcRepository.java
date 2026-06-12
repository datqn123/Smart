package com.example.smart_erp.custominterface.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Repository
public class CustomEntityJdbcRepository {

	private static final List<String> DEFAULT_ROLES = List.of("Owner", "Admin");

	private final JdbcTemplate jdbcTemplate;
	private final ObjectMapper objectMapper;

	public CustomEntityJdbcRepository(JdbcTemplate jdbcTemplate, ObjectMapper objectMapper) {
		this.jdbcTemplate = jdbcTemplate;
		this.objectMapper = objectMapper;
	}

	public Optional<EntityRow> findEntity(String entityKey) {
		List<EntityRow> rows = jdbcTemplate.query("""
				SELECT id, entity_key, label, description, status, draft_version, published_version, etag
				FROM custom_entities
				WHERE entity_key = ? AND archived_at IS NULL
				""", entityMapper(), entityKey);
		return rows.stream().findFirst();
	}

	public List<FieldRow> findFields(String entityKey) {
		return jdbcTemplate.query("""
				SELECT id::text AS id, entity_key, field_key, label, field_type, required, filterable, sortable,
				       searchable, order_index, helper_text, options_json::text AS options_json,
				       reference_json::text AS reference_json, validation_json::text AS validation_json,
				       default_value_json::text AS default_value_json, status
				FROM custom_entity_fields
				WHERE entity_key = ? AND status <> 'Archived'
				ORDER BY order_index ASC, id ASC
				""", fieldMapper(), entityKey);
	}

	public Optional<ViewRow> findView(String entityKey) {
		List<ViewRow> rows = jdbcTemplate.query("""
				SELECT entity_key, list_columns_json::text AS list_columns_json,
				       filter_fields_json::text AS filter_fields_json, default_sort,
				       form_sections_json::text AS form_sections_json
				FROM custom_entity_views
				WHERE entity_key = ?
				""", viewMapper(), entityKey);
		return rows.stream().findFirst();
	}

	public PermissionRow findPermissions(String entityKey) {
		List<ActionRolesRow> rows = jdbcTemplate.query("""
				SELECT action, roles_json::text AS roles_json
				FROM custom_entity_permissions
				WHERE entity_key = ?
				ORDER BY action ASC
				""", actionRolesMapper(), entityKey);
		return PermissionRow.from(rows);
	}

	public EntityRow replaceBundle(EntityRow current, String label, String description, List<CustomFieldRequest> fields,
			CustomViewRequest view, CustomPermissionRequest permissions, Integer userId) {
		int nextVersion = current.draftVersion() + 1;
		jdbcTemplate.update("""
				UPDATE custom_entities
				SET label = ?, description = ?, draft_version = ?, etag = ?, updated_by = ?, updated_at = now()
				WHERE entity_key = ? AND archived_at IS NULL
				""", label, description, nextVersion, entityEtag(current.key(), nextVersion), userId, current.key());

		jdbcTemplate.update("DELETE FROM custom_entity_fields WHERE entity_key = ?", current.key());
		List<CustomFieldRequest> safeFields = fields == null ? List.of() : fields;
		for (int index = 0; index < safeFields.size(); index++) {
			CustomFieldRequest field = safeFields.get(index);
			if (field == null) {
				continue;
			}
			jdbcTemplate.update("""
					INSERT INTO custom_entity_fields (
						entity_key, field_key, label, field_type, required, filterable, sortable, searchable,
						order_index, helper_text, options_json, reference_json, validation_json, default_value_json,
						status
					)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?::jsonb, ?::jsonb, ?::jsonb, ?)
					""", current.key(), field.fieldKey(), field.label(), field.type(), field.required(),
					field.filterable(), field.sortable(), field.searchable(), field.order() == null ? index : field.order(),
					field.helperText(), json(field.options(), "[]"), json(field.reference(), "{}"),
					json(field.validation(), "{}"), nullableJson(field.defaultValue()), defaultText(field.status(), "Active"));
		}

		CustomViewRequest safeView = view == null ? emptyView() : view;
		jdbcTemplate.update("DELETE FROM custom_entity_views WHERE entity_key = ?", current.key());
		jdbcTemplate.update("""
				INSERT INTO custom_entity_views (
					entity_key, list_columns_json, filter_fields_json, default_sort, form_sections_json
				)
				VALUES (?, ?::jsonb, ?::jsonb, ?, ?::jsonb)
				""", current.key(), json(safeView.listColumns(), "[]"), json(safeView.filterFields(), "[]"),
				safeView.defaultSort(), json(safeView.formSections(), "[]"));

		replacePermission(current.key(), "view", permissions == null ? null : permissions.view());
		replacePermission(current.key(), "create", permissions == null ? null : permissions.create());
		replacePermission(current.key(), "update", permissions == null ? null : permissions.update());
		replacePermission(current.key(), "delete", permissions == null ? null : permissions.delete());

		return findEntity(current.key()).orElseThrow();
	}

	public void publishSnapshot(String pageKey, EntityRow entity, int userId) {
		jdbcTemplate.update("""
				INSERT INTO custom_entity_versions (
					entity_key, version, page_key, entity_snapshot_json, fields_snapshot_json,
					views_snapshot_json, permissions_snapshot_json, published_by
				)
				SELECT e.entity_key, e.draft_version, ?,
				       jsonb_build_object(
				           'entityKey', e.entity_key,
				           'label', e.label,
				           'description', e.description,
				           'status', e.status,
				           'version', e.draft_version
				       ),
				       COALESCE((
				           SELECT jsonb_agg(to_jsonb(f) ORDER BY f.order_index, f.id)
				           FROM custom_entity_fields f
				           WHERE f.entity_key = e.entity_key AND f.status <> 'Archived'
				       ), '[]'::jsonb),
				       COALESCE((
				           SELECT to_jsonb(v)
				           FROM custom_entity_views v
				           WHERE v.entity_key = e.entity_key
				       ), '{}'::jsonb),
				       COALESCE((
				           SELECT jsonb_agg(to_jsonb(p) ORDER BY p.action)
				           FROM custom_entity_permissions p
				           WHERE p.entity_key = e.entity_key
				       ), '[]'::jsonb),
				       ?
				FROM custom_entities e
				WHERE e.entity_key = ? AND e.archived_at IS NULL
				ON CONFLICT (entity_key, version) DO NOTHING
				""", pageKey, userId, entity.key());
		jdbcTemplate.update("""
				UPDATE custom_entities
				SET status = 'Published', published_version = draft_version, published_at = now(),
				    updated_by = ?, updated_at = now()
				WHERE entity_key = ? AND archived_at IS NULL
				""", userId, entity.key());
	}

	public static String entityEtag(String key, int version) {
		return "entity-" + key + "-draft-" + version;
	}

	private void replacePermission(String entityKey, String action, List<String> roles) {
		jdbcTemplate.update("""
				INSERT INTO custom_entity_permissions(entity_key, action, roles_json)
				VALUES (?, ?, ?::jsonb)
				ON CONFLICT (entity_key, action)
				DO UPDATE SET roles_json = EXCLUDED.roles_json, updated_at = now()
				""", entityKey, action, rolesJson(roles));
	}

	private RowMapper<EntityRow> entityMapper() {
		return (rs, rowNum) -> new EntityRow(
				rs.getLong("id"),
				rs.getString("entity_key"),
				rs.getString("label"),
				rs.getString("description"),
				rs.getString("status"),
				rs.getInt("draft_version"),
				nullableInt(rs, "published_version"),
				rs.getString("etag"));
	}

	private RowMapper<FieldRow> fieldMapper() {
		return (rs, rowNum) -> new FieldRow(
				rs.getString("id"),
				rs.getString("entity_key"),
				rs.getString("field_key"),
				rs.getString("label"),
				rs.getString("field_type"),
				rs.getBoolean("required"),
				rs.getBoolean("filterable"),
				rs.getBoolean("sortable"),
				rs.getBoolean("searchable"),
				rs.getInt("order_index"),
				rs.getString("helper_text"),
				readJson(rs.getString("options_json"), objectMapper.createArrayNode()),
				readJson(rs.getString("reference_json"), objectMapper.createObjectNode()),
				readJson(rs.getString("validation_json"), objectMapper.createObjectNode()),
				readJson(rs.getString("default_value_json"), null),
				rs.getString("status"));
	}

	private RowMapper<ViewRow> viewMapper() {
		return (rs, rowNum) -> new ViewRow(
				rs.getString("entity_key"),
				readJson(rs.getString("list_columns_json"), objectMapper.createArrayNode()),
				readJson(rs.getString("filter_fields_json"), objectMapper.createArrayNode()),
				rs.getString("default_sort"),
				readJson(rs.getString("form_sections_json"), objectMapper.createArrayNode()));
	}

	private RowMapper<ActionRolesRow> actionRolesMapper() {
		return (rs, rowNum) -> new ActionRolesRow(
				rs.getString("action"),
				readJson(rs.getString("roles_json"), objectMapper.createArrayNode()));
	}

	private JsonNode readJson(String raw, JsonNode fallback) {
		if (raw == null) {
			return fallback;
		}
		try {
			return objectMapper.readTree(raw);
		}
		catch (Exception ex) {
			return fallback;
		}
	}

	private String json(JsonNode node, String fallback) {
		if (node == null || node.isNull()) {
			return fallback;
		}
		try {
			return node.toString();
		}
		catch (Exception ex) {
			return fallback;
		}
	}

	private String nullableJson(JsonNode node) {
		return node == null || node.isNull() ? null : json(node, null);
	}

	private String rolesJson(List<String> roles) {
		if (roles == null) {
			return "[]";
		}
		try {
			return objectMapper.writeValueAsString(roles);
		}
		catch (Exception ex) {
			return "[]";
		}
	}

	private static Integer nullableInt(ResultSet rs, String column) throws SQLException {
		int value = rs.getInt(column);
		return rs.wasNull() ? null : value;
	}

	private static String defaultText(String value, String fallback) {
		return value == null || value.isBlank() ? fallback : value;
	}

	private CustomViewRequest emptyView() {
		return new CustomViewRequest(objectMapper.createArrayNode(), objectMapper.createArrayNode(), null,
				objectMapper.createArrayNode(), "desktop");
	}

	public record EntityRow(long id, String key, String label, String description, String status, int draftVersion,
			Integer publishedVersion, String etag) {
	}

	public record FieldRow(String id, String entityKey, String fieldKey, String label, String type, boolean required,
			boolean filterable, boolean sortable, boolean searchable, int order, String helperText, JsonNode options,
			JsonNode reference, JsonNode validation, JsonNode defaultValue, String status) {
	}

	public record ViewRow(String entityKey, JsonNode listColumns, JsonNode filterFields, String defaultSort,
			JsonNode formSections) {
	}

	public record ActionRolesRow(String action, JsonNode roles) {
	}

	public record PermissionRow(List<String> view, List<String> create, List<String> update, List<String> delete) {
		public static PermissionRow from(List<ActionRolesRow> rows) {
			Map<String, List<String>> byAction = new LinkedHashMap<>();
			if (rows != null) {
				for (ActionRolesRow row : rows) {
					if (row != null && row.action() != null) {
						byAction.put(row.action(), roles(row.roles()));
					}
				}
			}
			return new PermissionRow(
					byAction.getOrDefault("view", DEFAULT_ROLES),
					byAction.getOrDefault("create", DEFAULT_ROLES),
					byAction.getOrDefault("update", DEFAULT_ROLES),
					byAction.getOrDefault("delete", DEFAULT_ROLES));
		}

		private static List<String> roles(JsonNode roles) {
			if (roles == null || !roles.isArray()) {
				return List.of();
			}
			List<String> out = new ArrayList<>();
			for (JsonNode role : roles) {
				if (role != null && role.isTextual()) {
					out.add(role.asText());
				}
			}
			return List.copyOf(out);
		}
	}
}
