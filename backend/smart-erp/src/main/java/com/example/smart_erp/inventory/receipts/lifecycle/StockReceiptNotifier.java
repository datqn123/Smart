package com.example.smart_erp.inventory.receipts.lifecycle;

import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

import com.example.smart_erp.notifications.repository.NotificationJdbcRepository;

/**
 * Thông báo phiếu nhập chờ duyệt — chỉ gửi tới role Admin (SRS PRD admin-notifications).
 */
@Component
public class StockReceiptNotifier {

	private final NotificationJdbcRepository notificationRepo;

	public StockReceiptNotifier(NotificationJdbcRepository notificationRepo) {
		this.notificationRepo = notificationRepo;
	}

	@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
	public void onStockReceiptPendingApproval(StockReceiptPendingApprovalEvent event) {
		notifyPendingApproval(event.actorUserId(), event.receiptId(), event.receiptCode());
	}

	public void notifyPendingApproval(int actorUserId, long receiptId, String receiptCode) {
		int refId = Math.toIntExact(receiptId);
		String title = "Phiếu nhập chờ duyệt";
		String message = "Phiếu " + receiptCode + " đã gửi duyệt — Admin vui lòng kiểm tra.";
		for (int recipientId : notificationRepo.findActiveAdminUserIds()) {
			if (recipientId == actorUserId) {
				continue;
			}
			notificationRepo.insertTyped(recipientId, "StockReceiptPendingApproval", title, message, "StockReceipt",
					refId);
		}
	}
}
