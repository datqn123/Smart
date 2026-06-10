package com.example.smart_erp.notifications.repository;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

/**
 * Bảng vật lý {@code notifications} (Flyway V1 — CREATE TABLE Notifications).
 */
@SuppressWarnings("null")
@Repository
public class NotificationJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public NotificationJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public record NotificationRow(
			long id,
			String notificationType,
			String title,
			String message,
			boolean read,
			String referenceType,
			Integer referenceId,
			Instant createdAt) {
	}

	public List<Integer> findActiveOwnerAdminUserIds() {
		String sql = """
				SELECT u.id
				FROM users u
				INNER JOIN roles r ON r.id = u.role_id
				WHERE r.name IN ('Owner', 'Admin')
				  AND u.status = 'Active'
				ORDER BY u.id ASC
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource(), (rs, row) -> rs.getInt("id"));
	}

	/** Chỉ role Admin (không gồm Owner) — thông báo chi tiết thiếu hàng phiếu xuất tay. */
	public List<Integer> findActiveAdminUserIds() {
		String sql = """
				SELECT u.id
				FROM users u
				INNER JOIN roles r ON r.id = u.role_id
				WHERE r.name = 'Admin'
				  AND u.status = 'Active'
				ORDER BY u.id ASC
				""";
		return namedJdbc.query(sql, new MapSqlParameterSource(), (rs, row) -> rs.getInt("id"));
	}

	public void insertSystemAlert(int recipientUserId, String title, String message, String referenceType,
			int referenceId) {
		insertTyped(recipientUserId, "SystemAlert", title, message, referenceType, referenceId);
	}

	/**
	 * Insert in-app notification. {@code notificationType} must match DB CHECK (see Flyway).
	 */
	public void insertTyped(int recipientUserId, String notificationType, String title, String message,
			String referenceType, int referenceId) {
		String sql = """
				INSERT INTO notifications (user_id, notification_type, title, message, is_read,
					reference_type, reference_id)
				VALUES (:_uid, :_ntype, :_title, :_message, FALSE,
					:_ref_type, :_ref_id)
				""";
		var src = new MapSqlParameterSource("_uid", recipientUserId).addValue("_ntype", notificationType)
				.addValue("_title", title).addValue("_message", message).addValue("_ref_type", referenceType)
				.addValue("_ref_id", referenceId);
		namedJdbc.update(sql, src);
	}

	public void insertPasswordResetRequested(int recipientUserId, String title, String message, long requestId) {
		int refId = Math.toIntExact(requestId);
		String sql = """
				INSERT INTO notifications (user_id, notification_type, title, message, is_read,
					reference_type, reference_id)
				VALUES (:_uid, 'PasswordResetRequest', :_title, :_message, FALSE,
					'StaffPasswordResetRequest', :_ref_id)
				""";
		var src = new MapSqlParameterSource("_uid", recipientUserId).addValue("_title", title)
				.addValue("_message", message).addValue("_ref_id", refId);
		namedJdbc.update(sql, src);
	}

	public void batchInsertPasswordResetRequested(List<Integer> recipientUserIds, String title, String message, long requestId) {
		int refId = Math.toIntExact(requestId);
		String sql = """
				INSERT INTO notifications (user_id, notification_type, title, message, is_read,
					reference_type, reference_id)
				VALUES (:_uid, 'PasswordResetRequest', :_title, :_message, FALSE,
					'StaffPasswordResetRequest', :_ref_id)
				""";
		MapSqlParameterSource[] batch = new MapSqlParameterSource[recipientUserIds.size()];
		for (int i = 0; i < recipientUserIds.size(); i++) {
			batch[i] = new MapSqlParameterSource("_uid", recipientUserIds.get(i))
					.addValue("_title", title)
					.addValue("_message", message)
					.addValue("_ref_id", refId);
		}
		namedJdbc.batchUpdate(sql, batch);
	}

	public long countForUser(int userId, Boolean unreadOnly) {
		boolean unread = Boolean.TRUE.equals(unreadOnly);
		String sql = "SELECT COUNT(*) FROM notifications WHERE user_id = :_uid "
				+ (unread ? "AND is_read = FALSE" : "");
		var src = new MapSqlParameterSource("_uid", userId);
		Long n = namedJdbc.queryForObject(sql, src, Long.class);
		return n != null ? n : 0L;
	}

	public long countUnreadForUser(int userId) {
		return countForUser(userId, true);
	}

	public List<NotificationRow> loadPage(int userId, Boolean unreadOnly, int page, int limit) {
		boolean unread = Boolean.TRUE.equals(unreadOnly);
		int offset = (page - 1) * limit;
		String sql = """
				SELECT id,
				       notification_type,
				       title,
				       message,
				       is_read,
				       reference_type,
				       reference_id,
				       created_at
				FROM notifications
				WHERE user_id = :_uid
				"""
				+ (unread ? "AND is_read = FALSE\n" : "")
				+ "ORDER BY created_at DESC LIMIT :_limit OFFSET :_offset";
		var src = new MapSqlParameterSource("_uid", userId).addValue("_limit", limit).addValue("_offset", offset);
		return namedJdbc.query(sql, src, (rs, i) -> {
			Integer rid = rs.getObject("reference_id") != null ? Integer.valueOf(rs.getInt("reference_id")) : null;
			Timestamp ts = rs.getTimestamp("created_at");
			Instant createdAt = ts != null ? ts.toInstant() : Instant.now();
			return new NotificationRow(
					rs.getLong("id"),
					rs.getString("notification_type"),
					rs.getString("title"),
					rs.getString("message"),
					rs.getBoolean("is_read"),
					rs.getString("reference_type"),
					rid,
					createdAt);
		});
	}

	public int forceMarkOwnedAsRead(int recipientUserId, long notificationId) {
		String sql = """
				UPDATE notifications SET is_read = TRUE, read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
				WHERE id = :_nid AND user_id = :_uid
				""";
		return namedJdbc.update(sql,
				new MapSqlParameterSource("_nid", notificationId).addValue("_uid", recipientUserId));
	}

	public int markAllRead(int recipientUserId) {
		String sql = """
				UPDATE notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
				WHERE user_id = :_uid AND is_read = FALSE
				""";
		return namedJdbc.update(sql, new MapSqlParameterSource("_uid", recipientUserId));
	}
}
