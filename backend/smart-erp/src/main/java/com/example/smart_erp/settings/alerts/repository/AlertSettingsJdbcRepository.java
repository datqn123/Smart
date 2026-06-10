package com.example.smart_erp.settings.alerts.repository;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.settings.alerts.response.AlertSettingItemData;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Persistence for table {@code alertsettings} (created from Flyway V1 {@code CREATE TABLE AlertSettings}).
 */
@SuppressWarnings("null")
@Repository
public class AlertSettingsJdbcRepository {

	private static final TypeReference<List<String>> RECIPIENTS_LIST = new TypeReference<>() {
	};

	private final NamedParameterJdbcTemplate namedJdbc;
	private final ObjectMapper objectMapper;
	private final RowMapper<AlertSettingItemData> rowMapper;

	public AlertSettingsJdbcRepository(NamedParameterJdbcTemplate namedJdbc, ObjectMapper objectMapper) {
		this.namedJdbc = namedJdbc;
		this.objectMapper = objectMapper;
		this.rowMapper = (rs, i) -> {
			Timestamp ua = rs.getTimestamp("updated_at");
			String recipientsJson = rs.getString("recipients");
			List<String> recipients = null;
			if (recipientsJson != null && !recipientsJson.isBlank()) {
				try {
					recipients = this.objectMapper.readValue(recipientsJson, RECIPIENTS_LIST);
				}
				catch (Exception e) {
					// fallback: keep null to avoid crashing list; data can be fixed by admin later
					recipients = null;
				}
			}
			return new AlertSettingItemData(
					rs.getLong("id"),
					rs.getString("alert_type"),
					(BigDecimal) rs.getObject("threshold_value"),
					rs.getString("channel"),
					rs.getString("frequency"),
					rs.getBoolean("is_enabled"),
					recipients,
					ua != null ? ua.toInstant() : Instant.EPOCH);
		};
	}

	public List<AlertSettingItemData> list(Integer ownerId, String alertType, Boolean isEnabled) {
		StringBuilder sb = new StringBuilder("""
				SELECT
				  id, alert_type, threshold_value, channel, frequency, is_enabled, recipients, updated_at
				FROM alertsettings
				WHERE 1=1
				""");
		var src = new MapSqlParameterSource();
		if (ownerId != null) {
			sb.append(" AND owner_id = :ownerId");
			src.addValue("ownerId", ownerId);
		}
		if (alertType != null && !alertType.isBlank()) {
			sb.append(" AND alert_type = :alertType");
			src.addValue("alertType", alertType);
		}
		if (isEnabled != null) {
			sb.append(" AND is_enabled = :isEnabled");
			src.addValue("isEnabled", isEnabled);
		}
		sb.append(" ORDER BY id ASC");
		return namedJdbc.query(sb.toString(), src, rowMapper);
	}

	public Optional<String> findAlertTypeByIdAndOwner(long id, int ownerId) {
		String sql = """
				SELECT alert_type
				FROM alertsettings
				WHERE id = :id AND owner_id = :ownerId
				LIMIT 1
				""";
		var src = new MapSqlParameterSource("id", id).addValue("ownerId", ownerId);
		var list = namedJdbc.query(sql, src, (rs, i) -> rs.getString("alert_type"));
		return list.isEmpty() ? Optional.empty() : Optional.ofNullable(list.getFirst());
	}

	public Optional<AlertSettingItemData> insert(int ownerId, String alertType, BigDecimal thresholdValue, String channel, String frequency,
			boolean isEnabled, String recipientsJson) {
		String sql = """
				INSERT INTO alertsettings (
				  owner_id, alert_type, threshold_value, channel, frequency, is_enabled, recipients, created_at, updated_at
				)
				VALUES (
				  :ownerId, :alertType, :thresholdValue, :channel, :frequency, :isEnabled,
				  CASE WHEN :recipientsJson IS NULL THEN NULL ELSE CAST(:recipientsJson AS jsonb) END,
				  CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
				)
				RETURNING id, alert_type, threshold_value, channel, frequency, is_enabled, recipients, updated_at
				""";
		var src = new MapSqlParameterSource()
				.addValue("ownerId", ownerId)
				.addValue("alertType", alertType)
				.addValue("thresholdValue", thresholdValue)
				.addValue("channel", channel)
				.addValue("frequency", frequency)
				.addValue("isEnabled", isEnabled)
				.addValue("recipientsJson", recipientsJson);
		var list = namedJdbc.query(sql, src, rowMapper);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public Optional<AlertSettingItemData> patchByIdAndOwner(long id, int ownerId, BigDecimal thresholdValue, boolean setThresholdValue, String channel,
			String frequency, Boolean isEnabled, String recipientsJson, boolean setRecipients) {
		String sql = """
				UPDATE alertsettings
				SET
				  threshold_value = CASE WHEN :setThresholdValue THEN :thresholdValue ELSE threshold_value END,
				  channel = COALESCE(:channel, channel),
				  frequency = COALESCE(:frequency, frequency),
				  is_enabled = COALESCE(:isEnabled, is_enabled),
				  recipients = CASE
				    WHEN :setRecipients = FALSE THEN recipients
				    WHEN :recipientsJson IS NULL THEN NULL
				    ELSE CAST(:recipientsJson AS jsonb)
				  END,
				  updated_at = CURRENT_TIMESTAMP
				WHERE id = :id AND owner_id = :ownerId
				RETURNING id, alert_type, threshold_value, channel, frequency, is_enabled, recipients, updated_at
				""";
		var src = new MapSqlParameterSource()
				.addValue("id", id)
				.addValue("ownerId", ownerId)
				.addValue("setThresholdValue", setThresholdValue)
				.addValue("thresholdValue", thresholdValue)
				.addValue("channel", channel)
				.addValue("frequency", frequency)
				.addValue("isEnabled", isEnabled)
				.addValue("setRecipients", setRecipients)
				.addValue("recipientsJson", recipientsJson);
		var list = namedJdbc.query(sql, src, rowMapper);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public int softDisableByIdAndOwner(long id, int ownerId) {
		String sql = """
				UPDATE alertsettings
				SET is_enabled = FALSE,
				    updated_at = CURRENT_TIMESTAMP
				WHERE id = :id AND owner_id = :ownerId
				""";
		return namedJdbc.update(sql, new MapSqlParameterSource("id", id).addValue("ownerId", ownerId));
	}
}

