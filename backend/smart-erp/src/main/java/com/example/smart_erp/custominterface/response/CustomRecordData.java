package com.example.smart_erp.custominterface.response;

import java.time.Instant;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomRecordData(
		long id,
		String entityKey,
		int publishedVersion,
		JsonNode values,
		String state,
		Instant createdAt,
		Instant updatedAt) {
}
