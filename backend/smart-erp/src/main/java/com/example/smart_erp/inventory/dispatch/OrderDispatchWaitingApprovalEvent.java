package com.example.smart_erp.inventory.dispatch;

public record OrderDispatchWaitingApprovalEvent(int actorUserId, long dispatchId, String orderCode) {
}
