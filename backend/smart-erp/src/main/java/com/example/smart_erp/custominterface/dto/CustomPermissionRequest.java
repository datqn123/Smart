package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomPermissionRequest(
		List<String> view,
		List<String> create,
		List<String> update,
		List<String> delete) {
}
