package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomPermissionData(
		List<String> view,
		List<String> create,
		List<String> update,
		List<String> delete) {
}
