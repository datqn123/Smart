package com.example.smart_erp.ai.catalogdraft.dto;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.validation.constraints.NotNull;

public record CatalogDraftPatchRequest(@NotNull JsonNode rows, JsonNode columns) {
}
