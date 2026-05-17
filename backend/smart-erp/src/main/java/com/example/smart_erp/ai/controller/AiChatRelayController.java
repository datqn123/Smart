package com.example.smart_erp.ai.controller;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/v1/ai")
public class AiChatRelayController {

	private static final Logger log = LoggerFactory.getLogger(AiChatRelayController.class);

	public record AiChatRelayRequest(String message, String conversationId, String interactionMode) {
	}

	private final String pythonBaseUrl;

	private final HttpClient httpClient;

	private final ObjectMapper objectMapper;

	private final ExecutorService sseIoExecutor = Executors.newCachedThreadPool();

	public AiChatRelayController(@Value("${app.ai.python.base-url}") String pythonBaseUrl, ObjectMapper objectMapper) {
		this.pythonBaseUrl = normalizePythonBaseUrl(pythonBaseUrl);
		this.httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
		this.objectMapper = objectMapper;
	}

	private static String normalizePythonBaseUrl(String raw) {
		String s = Objects.requireNonNull(raw, "pythonBaseUrl").trim();
		s = s.replaceAll("/+$", "");
		if (!(s.startsWith("http://") || s.startsWith("https://"))) {
			s = "http://" + s;
		}
		return s;
	}

	/**
	 * Some JDK {@link Exception}s use a null {@link Exception#getMessage()} (e.g. wrapped IO); avoid a useless
	 * {@code "Relay error"} in the SSE payload.
	 */
	private static String relayErrorDetail(Throwable e) {
		String m = e.getMessage();
		if (m != null && !m.isBlank()) {
			return m;
		}
		Throwable c = e.getCause();
		if (c != null) {
			String cm = c.getMessage();
			if (cm != null && !cm.isBlank()) {
				return e.getClass().getSimpleName() + ": " + cm;
			}
			return e.getClass().getSimpleName() + " (" + c.getClass().getSimpleName() + ")";
		}
		return e.getClass().getSimpleName()
				+ " — kiểm tra service Python (uvicorn) và cổng khớp AI_PYTHON_BASE_URL / app.ai.python.base-url (mặc định Spring: 9000).";
	}

	/**
	 * Relay authenticated SSE: browser → Spring (JWT) → FastAPI LangGraph (same Bearer).
	 * Request body: message + optional conversationId (thread). Identity metadata is taken from JWT.
	 */
	@PostMapping(path = "/chat/stream", consumes = MediaType.APPLICATION_JSON_VALUE,
			produces = MediaType.TEXT_EVENT_STREAM_VALUE)
	public SseEmitter streamPost(@RequestBody AiChatRelayRequest body, @AuthenticationPrincipal Jwt jwt,
			HttpServletRequest httpRequest) {
		SseEmitter emitter = new SseEmitter(0L);
		String authz = httpRequest.getHeader("Authorization");
		if (authz == null || !authz.startsWith("Bearer ")) {
			sseIoExecutor.execute(() -> {
				try {
					emitter.send(SseEmitter.event().name("error").data("Thiếu Authorization Bearer."));
					emitter.complete();
				}
				catch (Exception ignored) {
					emitter.completeWithError(ignored);
				}
			});
			return emitter;
		}

		String userId = jwt.getClaimAsString("user_id");
		if (userId == null || userId.isBlank()) {
			userId = jwt.getSubject();
		}
		String tenantId = jwt.getClaimAsString("tenant_id");
		if (tenantId == null || tenantId.isBlank()) {
			tenantId = "1";
		}

		String correlationId = UUID.randomUUID().toString();
		String jsonBody;
		try {
			ObjectNode root = objectMapper.createObjectNode();
			root.put("message", body.message());
			ObjectNode md = objectMapper.createObjectNode();
			md.put("user_id", userId);
			md.put("tenant_id", tenantId);
			if (body.conversationId() != null && !body.conversationId().isBlank()) {
				md.put("thread_id", body.conversationId());
			}
			md.put("schema_version", "v1");
			root.set("metadata", md);
			ObjectNode options = root.putObject("options");
			String mode = body.interactionMode();
			if (mode != null && !mode.isBlank() && !"auto".equalsIgnoreCase(mode.trim())) {
				options.put("interaction_mode", mode.trim().toLowerCase());
			}
			jsonBody = objectMapper.writeValueAsString(root);
		}
		catch (Exception e) {
			sseIoExecutor.execute(() -> {
				try {
					emitter.send(SseEmitter.event().name("error").data("Không thể dựng payload AI."));
					emitter.complete();
				}
				catch (Exception ignored) {
					emitter.completeWithError(ignored);
				}
			});
			return emitter;
		}

		URI uri = URI.create(pythonBaseUrl + "/api/v1/ai/chat/stream");
		final String relayTarget = uri.toString();
		final String bodyJson = jsonBody;

		sseIoExecutor.execute(() -> {
			try {
				HttpRequest req = HttpRequest.newBuilder(uri).version(Version.HTTP_1_1).timeout(Duration.ofMinutes(5))
						.header("Accept", "text/event-stream")
						.header("Content-Type", "application/json")
						.header("Authorization", authz)
						.header("X-Correlation-Id", correlationId)
						.POST(HttpRequest.BodyPublishers.ofString(bodyJson, StandardCharsets.UTF_8))
						.build();

				HttpResponse<InputStream> res = httpClient.send(req, HttpResponse.BodyHandlers.ofInputStream());
				int code = res.statusCode();
				if (code < 200 || code >= 300) {
					String detail;
					try (InputStream errIn = res.body()) {
						byte[] snippet = errIn.readNBytes(2048);
						detail =
								new String(snippet, StandardCharsets.UTF_8).replace('\r', ' ').replace('\n', ' ');
					}
					String msg = "Python AI HTTP " + code
							+ " — kiểm tra AI_PYTHON_BASE_URL và service ai_python. Chi tiết: " + detail;
					emitter.send(SseEmitter.event().name("error").data(msg));
					emitter.complete();
					return;
				}

				try (InputStream upstream = res.body();
						BufferedReader reader =
								new BufferedReader(new InputStreamReader(upstream, StandardCharsets.UTF_8))) {
					String line;
					String event = null;
					StringBuilder data = new StringBuilder();

					while ((line = reader.readLine()) != null) {
						if (line.isEmpty()) {
							if (event != null) {
								String payload = data.toString();
								emitter.send(SseEmitter.event().name(event).data(payload));
								if ("done".equals(event)) {
									emitter.complete();
									return;
								}
							}
							event = null;
							data.setLength(0);
							continue;
						}
						if (line.startsWith("event:")) {
							event = line.substring("event:".length()).trim();
							continue;
						}
						if (line.startsWith("data:")) {
							String chunk = line.substring("data:".length());
							if (chunk.startsWith(" ")) {
								chunk = chunk.substring(1);
							}
							if (!data.isEmpty()) {
								data.append("\n");
							}
							data.append(chunk);
						}
					}

					emitter.complete();
				}
			}
			catch (Exception e) {
				log.error("AI relay failed: {}", relayTarget, e);
				try {
					emitter.send(SseEmitter.event().name("error").data(relayErrorDetail(e)));
				}
				catch (Exception ignored) {
					// ignore secondary failure
				}
				emitter.completeWithError(e);
			}
		});

		return emitter;
	}
}
