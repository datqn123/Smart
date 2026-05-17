package com.example.smart_erp.ai.inventorydraft.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record InventoryDraftCommitResult(
		boolean success,
		String message,
		Integer createdReceiptId,
		String receiptCode,
		JsonNode draft) {
}
