package com.example.smart_erp.inventory.receipts.lifecycle;

public record StockReceiptPendingApprovalEvent(int actorUserId, long receiptId, String receiptCode) {
}
