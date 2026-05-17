package com.example.smart_erp.ai.inventorydraft;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@SuppressWarnings("null")
@Repository
public class AiInventoryDraftJdbcRepository {

	public record DraftRow(
			UUID id,
			String userId,
			String tenantId,
			String conversationId,
			String entityType,
			String status,
			JsonNode payload,
			JsonNode commitResult,
			Instant createdAt,
			Instant updatedAt,
			Instant expiresAt) {
	}

	private final NamedParameterJdbcTemplate jdbc;
	private final ObjectMapper objectMapper;
	private final RowMapper<DraftRow> rowMapper = (rs, n) -> mapRow(rs);

	public AiInventoryDraftJdbcRepository(NamedParameterJdbcTemplate jdbc, ObjectMapper objectMapper) {
		this.jdbc = jdbc;
		this.objectMapper = objectMapper;
	}

	public UUID insert(
			String userId,
			String tenantId,
			String conversationId,
			String entityType,
			JsonNode payload,
			Instant expiresAt) {
		UUID id = UUID.randomUUID();
		String sql = """
				INSERT INTO ai_inventory_draft (
				  id, user_id, tenant_id, conversation_id, entity_type, status, payload, expires_at
				) VALUES (
				  :id, :userId, :tenantId, :conversationId, :entityType, 'draft', CAST(:payload AS jsonb), :expiresAt
				)
				""";
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("id", id);
		p.addValue("userId", userId);
		p.addValue("tenantId", tenantId);
		p.addValue("conversationId", conversationId);
		p.addValue("entityType", entityType);
		p.addValue("payload", writeJson(payload));
		p.addValue("expiresAt", Timestamp.from(expiresAt));
		jdbc.update(sql, p);
		return id;
	}

	public Optional<DraftRow> findByIdForUser(UUID id, String userId) {
		String sql = """
				SELECT id, user_id, tenant_id, conversation_id, entity_type, status,
				       payload, commit_result, created_at, updated_at, expires_at
				FROM ai_inventory_draft
				WHERE id = :id AND user_id = :userId
				""";
		List<DraftRow> rows = jdbc.query(sql, Map.of("id", id, "userId", userId), rowMapper);
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public boolean updatePayload(UUID id, String userId, JsonNode payload) {
		String sql = """
				UPDATE ai_inventory_draft
				SET payload = CAST(:payload AS jsonb), updated_at = NOW()
				WHERE id = :id AND user_id = :userId AND status = 'draft'
				  AND expires_at > NOW()
				""";
		int n = jdbc.update(sql, Map.of("id", id, "userId", userId, "payload", writeJson(payload)));
		return n > 0;
	}

	public void updateAfterCommit(UUID id, String userId, JsonNode payload, JsonNode commitResult, String status) {
		String sql = """
				UPDATE ai_inventory_draft
				SET payload = CAST(:payload AS jsonb),
				    commit_result = CAST(:commitResult AS jsonb),
				    status = :status,
				    updated_at = NOW()
				WHERE id = :id AND user_id = :userId
				""";
		jdbc.update(sql, Map.of(
				"id", id,
				"userId", userId,
				"payload", writeJson(payload),
				"commitResult", writeJson(commitResult),
				"status", status));
	}

	private DraftRow mapRow(ResultSet rs) throws SQLException {
		return new DraftRow(
				(UUID) rs.getObject("id"),
				rs.getString("user_id"),
				rs.getString("tenant_id"),
				rs.getString("conversation_id"),
				rs.getString("entity_type"),
				rs.getString("status"),
				readJson(rs.getString("payload")),
				readJson(rs.getString("commit_result")),
				rs.getTimestamp("created_at").toInstant(),
				rs.getTimestamp("updated_at").toInstant(),
				rs.getTimestamp("expires_at").toInstant());
	}

	private String writeJson(JsonNode node) {
		try {
			return objectMapper.writeValueAsString(node == null ? objectMapper.nullNode() : node);
		}
		catch (Exception e) {
			throw new IllegalArgumentException("Invalid JSON payload", e);
		}
	}

	private JsonNode readJson(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		try {
			return objectMapper.readTree(raw);
		}
		catch (Exception e) {
			throw new IllegalStateException("Corrupt JSONB in ai_inventory_draft", e);
		}
	}
}
