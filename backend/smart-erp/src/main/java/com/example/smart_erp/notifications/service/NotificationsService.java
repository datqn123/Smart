package com.example.smart_erp.notifications.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.notifications.repository.NotificationJdbcRepository;
import com.example.smart_erp.notifications.repository.NotificationJdbcRepository.NotificationRow;
import com.example.smart_erp.notifications.response.NotificationItemData;
import com.example.smart_erp.notifications.response.NotificationsPageData;

@Service
public class NotificationsService {

	private final NotificationJdbcRepository notificationJdbcRepository;

	public NotificationsService(NotificationJdbcRepository notificationJdbcRepository) {
		this.notificationJdbcRepository = notificationJdbcRepository;
	}

	@Transactional(readOnly = true)
	public NotificationsPageData list(int viewerUserId, int page, int limit, Boolean unreadOnly) {
		long total = notificationJdbcRepository.countForUser(viewerUserId, unreadOnly);
		long unreadTotal = notificationJdbcRepository.countUnreadForUser(viewerUserId);
		List<NotificationRow> rows = notificationJdbcRepository.loadPage(viewerUserId, unreadOnly, page, limit);
		List<NotificationItemData> items = rows.stream().map(NotificationsService::toItem).toList();
		return new NotificationsPageData(items, page, limit, total, unreadTotal);
	}

	private static NotificationItemData toItem(NotificationRow r) {
		return new NotificationItemData(r.id(), r.notificationType(), r.title(), r.message(), r.read(), r.referenceType(),
				r.referenceId(), r.createdAt());
	}

	@Transactional
	public void markOwnedAsRead(int viewerUserId, long notificationId) {
		int n = notificationJdbcRepository.forceMarkOwnedAsRead(viewerUserId, notificationId);
		if (n == 0) {
			throw new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy thông báo");
		}
	}

	@Transactional
	public void markAllAsRead(int viewerUserId) {
		notificationJdbcRepository.markAllRead(viewerUserId);
	}

	/**
	 * Gọi trong transaction Task004 §1 sau khi INSERT request.
	 */
	public void broadcastPasswordResetRequestToOwnerAdmin(long passwordResetRequestId, String staffUsername) {
		List<Integer> recipients = notificationJdbcRepository.findActiveOwnerAdminUserIds();
		if (recipients.isEmpty()) {
			return;
		}
		String title = "Yêu cầu đặt lại mật khẩu";
		String msg = String.format("Nhân viên %s đã gửi yêu cầu đặt lại mật khẩu.", staffUsername.strip());
		notificationJdbcRepository.batchInsertPasswordResetRequested(recipients, title, msg, passwordResetRequestId);
	}
}
