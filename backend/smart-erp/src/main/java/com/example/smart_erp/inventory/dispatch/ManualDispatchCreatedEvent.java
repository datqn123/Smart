package com.example.smart_erp.inventory.dispatch;

public record ManualDispatchCreatedEvent(int actorUserId, long dispatchId, String dispatchCode, String referenceLabel) {
}
