package com.example.smart_erp.inventory.dispatch;

import java.util.List;

public record StockDispatchShortageEvent(int actorUserId, long dispatchId, String dispatchCode, List<String> shortageLines) {
}
