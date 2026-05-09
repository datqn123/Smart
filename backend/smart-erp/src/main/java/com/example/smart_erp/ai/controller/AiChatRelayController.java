package com.example.smart_erp.ai.controller;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Objects;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/v1/ai")
public class AiChatRelayController {

	private final String pythonBaseUrl;

	private final HttpClient httpClient;

	private final ExecutorService sseIoExecutor = Executors.newCachedThreadPool();

	public AiChatRelayController(@Value("${app.ai.python.base-url}") String pythonBaseUrl) {
		this.pythonBaseUrl = normalizePythonBaseUrl(pythonBaseUrl);
		this.httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
	}

	/**
	 * Avoid {@code URI.create("localhost:9000/...")} (opaque / wrong scheme) and trim trailing slashes.
	 * Uvicorn expects cleartext HTTP/1.1; {@code https://} to port 9000 causes TLS bytes → "Invalid HTTP request".
	 */
	private static String normalizePythonBaseUrl(String raw) {
		String s = Objects.requireNonNull(raw, "pythonBaseUrl").trim();
		s = s.replaceAll("/+$", "");
		if (!(s.startsWith("http://") || s.startsWith("https://"))) {
			s = "http://" + s;
		}
		return s;
	}

	@GetMapping(path = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
	public SseEmitter stream(@RequestParam("q") String q, @RequestParam(value = "cid", required = false) String cid) {
		SseEmitter emitter = new SseEmitter(0L);
		String encoded = URLEncoder.encode(q, StandardCharsets.UTF_8);
		String cidParam = cid == null || cid.isBlank() ? "" : ("&cid=" + URLEncoder.encode(cid, StandardCharsets.UTF_8));
		URI uri = URI.create(pythonBaseUrl + "/v1/chat/stream?q=" + encoded + cidParam);

		sseIoExecutor.execute(() -> {
			try {
				HttpRequest req = HttpRequest.newBuilder(uri).version(Version.HTTP_1_1).timeout(Duration.ofMinutes(5))
						.header("Accept", "text/event-stream").GET().build();

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
							+ " — đặt AI_PYTHON_BASE_URL=http://127.0.0.1:9000 (uvicorn chỉ nhận HTTP thường, không "
							+ "https:// tới cổng 9000 — TLS sẽ gây lỗi \"Invalid HTTP request\" trên Python). Chi tiết: "
							+ detail;
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
							// Preserve leading spaces in streamed deltas.
							// SSE allows an optional single space after "data:".
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
			} catch (Exception e) {
				try {
					emitter.send(SseEmitter.event().name("error").data(Objects.toString(e.getMessage(), "Relay error")));
				} catch (Exception ignored) {
					// ignore secondary failure
				}
				emitter.completeWithError(e);
			}
		});

		return emitter;
	}
}

