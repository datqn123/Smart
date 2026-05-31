package com.example.smart_erp.auth.api;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Locks Postman sample JSON under {@code docs/postman/} for Task003 — same envelope shape as
 * {@link Task001LoginPostmanBodyContractTest}: {@code _description}, {@code request}, {@code headers}, {@code body}.
 */
class Task003RefreshPostmanBodyContractTest {

	private static final ObjectMapper MAPPER = new ObjectMapper();

	private static final String TASK003_PATH = "/api/v1/auth/refresh";

	@Test
	void validBody_matchesEnvelopeShape_andEndpoint() throws IOException {
		JsonNode root = readPostmanEnvelope("Task003_refresh.valid.body.json");
		assertTask003Endpoint(root);
		assertContentTypeHeader(root);
		RefreshRequestBody parsed = MAPPER.treeToValue(root.required("body"), RefreshRequestBody.class);
		assertThat(parsed.refreshToken()).isNotBlank();
	}

	@Test
	void invalidMissingRefresh_bodyHasNoRefreshTokenKey() throws IOException {
		JsonNode root = readPostmanEnvelope("Task003_refresh.invalid.missing-refresh.body.json");
		assertTask003Endpoint(root);
		assertContentTypeHeader(root);
		JsonNode body = root.required("body");
		assertThat(body.has("refreshToken")).as("missing refreshToken field").isFalse();
	}

	@Test
	void invalidEmptyRefresh_parsesBlankToken() throws IOException {
		JsonNode root = readPostmanEnvelope("Task003_refresh.invalid.empty-refresh.body.json");
		assertTask003Endpoint(root);
		assertContentTypeHeader(root);
		RefreshRequestBody parsed = MAPPER.treeToValue(root.required("body"), RefreshRequestBody.class);
		assertThat(parsed.refreshToken()).isEmpty();
	}

	private static void assertTask003Endpoint(JsonNode root) {
		JsonNode req = root.required("request");
		assertThat(req.required("method").asText()).as("request.method").isEqualTo("POST");
		assertThat(req.required("path").asText()).as("request.path").isEqualTo(TASK003_PATH);
		String url = req.required("url").asText();
		assertThat(url).as("request.url").endsWith(TASK003_PATH);
		assertThat(url).as("request.url").startsWith("http://");
	}

	private static void assertContentTypeHeader(JsonNode root) {
		assertThat(root.path("headers").path("Content-Type").asText()).isEqualTo("application/json");
	}

	private static JsonNode readPostmanEnvelope(String fileName) throws IOException {
		return MAPPER.readTree(readPostmanSample(fileName));
	}

	private static String readPostmanSample(String fileName) throws IOException {
		Path dir = resolvePostmanDir();
		Path p = dir.resolve(fileName);
		assertThat(p).as("Postman sample missing: %s (expected under docs/postman/)", p).exists();
		return Files.readString(p, StandardCharsets.UTF_8);
	}

	private static Path resolvePostmanDir() {
		Path cwd = Path.of("").toAbsolutePath();
		Path direct = cwd.resolve("docs/postman");
		if (Files.isDirectory(direct)) {
			return direct;
		}
		Path fromRepoRoot = cwd.resolve("docs/backend/smart-erp/postman");
		if (Files.isDirectory(fromRepoRoot)) {
			return fromRepoRoot;
		}
		Path fromBackendModule = cwd.resolve("../../docs/backend/smart-erp/postman").normalize();
		if (Files.isDirectory(fromBackendModule)) {
			return fromBackendModule;
		}
		return direct;
	}
}
