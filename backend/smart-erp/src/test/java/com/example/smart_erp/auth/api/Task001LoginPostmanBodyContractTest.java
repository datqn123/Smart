package com.example.smart_erp.auth.api;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import com.example.smart_erp.auth.AuthTask001Fixtures;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Locks Postman sample JSON under {@code docs/postman/} for Task001: each file must include
 * full {@code request} (method, path, url) plus {@code body} — see {@link #assertTask001Endpoint(JsonNode)}.
 * Tài khoản dev: {@link AuthTask001Fixtures}.
 */
class Task001LoginPostmanBodyContractTest {

	private static final ObjectMapper MAPPER = new ObjectMapper();

	private static final String TASK001_PATH = "/api/v1/auth/login";

	@Test
	void validBody_matchesTask001ExampleShape_andEndpoint() throws IOException {
		JsonNode root = readPostmanEnvelope("Task001_login.valid.body.json");
		assertTask001Endpoint(root);
		assertContentTypeHeader(root);
		LoginRequestBody parsed = MAPPER.treeToValue(root.required("body"), LoginRequestBody.class);
		assertThat(parsed.email()).isEqualTo(AuthTask001Fixtures.DEV_OWNER_EMAIL);
		assertThat(parsed.password()).isEqualTo(AuthTask001Fixtures.DEV_OWNER_PASSWORD);
	}

	@Test
	void invalidBodies_matchEndpoint_andParseBody() throws IOException {
		for (String file : new String[] {
				"Task001_login.invalid.missing-fields.body.json",
				"Task001_login.invalid.short-password.body.json" }) {
			JsonNode root = readPostmanEnvelope(file);
			assertTask001Endpoint(root);
			assertContentTypeHeader(root);
			LoginRequestBody parsed = MAPPER.treeToValue(root.required("body"), LoginRequestBody.class);
			assertThat(parsed).isNotNull();
		}
	}

	private static void assertTask001Endpoint(JsonNode root) {
		JsonNode req = root.required("request");
		assertThat(req.required("method").asText()).as("request.method").isEqualTo("POST");
		assertThat(req.required("path").asText()).as("request.path").isEqualTo(TASK001_PATH);
		String url = req.required("url").asText();
		assertThat(url).as("request.url").endsWith(TASK001_PATH);
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

	/**
	 * Supports {@code mvn test} from {@code backend/smart-erp} (IDE / CI usual) or from repo root with
	 * {@code mvn -f backend/smart-erp/pom.xml test}.
	 */
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
