# Voice Processing Feature — Implementation Plan

## Goal
Cho phép người dùng gửi tin nhắn thoại trong AI chat. Backend chuyển audio → text qua **FPT Cloud Whisper** (OpenAI-compatible STT), rồi đưa transcript vào pipeline chat hiện có như tin nhắn text.

## Architecture Decision
- **Backend STT (FPT Whisper)** — Không dùng Web Speech API trên browser (RULES cũ UC13); audio gửi server, Python gọi `FPT.AI-whisper-medium`.
- **Cùng gateway LLM** — `https://mkp-api.fptcloud.com`, cùng pattern `openai.OpenAI` như `ai_python/scripts/fpt_openai_stream_example.py`.
- **Tap toggle UI** — Bấm mic để ghi, bấm lại để dừng và gửi.
- **WAV trên wire** — FE chuyển `webm` → WAV trước upload; API Whisper chấp nhận thêm MP3 nếu cần debug/script.

---

## STT Provider — FPT Cloud (Whisper)

| Mục | Giá trị |
|-----|---------|
| Base URL | `https://mkp-api.fptcloud.com` (giống `LLM_BASE_URL`) |
| Model | `FPT.AI-whisper-medium` |
| API | `client.audio.transcriptions.create` (OpenAI Python SDK) |
| Ngôn ngữ mặc định | `vi` (ERP tiếng Việt) |
| Response | `response_format="json"` → đọc `response.text` |

**Mẫu tham chiếu (đúng contract SDK — không truyền `file` là bytes trần):**

```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.stt_api_key,  # hoặc inherit LLM_API_KEY
    base_url=settings.stt_base_url.rstrip("/"),
)

with open("recording.wav", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model="FPT.AI-whisper-medium",
        file=("recording.wav", audio_file, "audio/wav"),  # tuple: tên + stream + MIME
        response_format="json",
        language="vi",
    )
transcript = (response.text or "").strip()
```

**Lưu ý triển khai:**
- Dùng **tuple `(filename, file, mime)`** hoặc file object mở — tránh `file=bytes` (snippet mẫu ngoài repo dễ lỗi MIME/format).
- `language` mặc định **`vi`**, không `en`.
- Timeout HTTP riêng cho STT (gợi ý 30–60s), tách `LLM_HTTP_REQUEST_TIMEOUT` (120s).
- Script smoke: `ai_python/scripts/fpt_whisper_transcribe_example.py` (cùng style `fpt_openai_stream_example.py`).

---

## Phase 1: Backend STT Client

### 1.1 `app/config/settings.py` — `SttSettings` (tách khỏi `LlmSettings`)

Prefix env: `STT_`. Có thể **inherit** credential gateway khi field STT trống.

| Setting | Default | Description |
|---------|---------|-------------|
| `stt_enabled` | `False` | Bật/tắt STT toàn cục |
| `stt_base_url` | `""` | Trống → dùng `LLM_BASE_URL` |
| `stt_api_key` | `None` | Trống → dùng `LLM_API_KEY` |
| `stt_model` | `FPT.AI-whisper-medium` | Model Whisper trên FPT |
| `stt_language` | `"vi"` | Ngôn ngữ gửi API |
| `stt_response_format` | `"json"` | `json` \| `text` \| `verbose_json` (gateway cho phép) |
| `stt_max_audio_seconds` | `60` | Giới hạn độ dài ghi âm |
| `stt_max_upload_bytes` | `10485760` | 10 MB |
| `stt_http_timeout_seconds` | `45.0` | Timeout transcribe |

`load_stt_settings()` + helper `resolve_stt_credentials(llm: LlmSettings, stt: SttSettings)`.

### 1.2 `requirements.txt`
Thêm dependency tường minh (đã có transitive qua `langchain-openai`, nhưng STT module import trực tiếp):

```
openai>=1.40.0,<2.0.0
```

### 1.3 `app/stt/__init__.py`
Export `SttClient` protocol và `build_stt_client()`.

### 1.4 `app/stt/protocol.py`
```python
class SttClient(Protocol):
    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str = "recording.wav",
        language: str | None = None,
    ) -> str:
        """Transcribe audio bytes to plain text."""
```

### 1.5 `app/stt/fpt_whisper.py` — Implementation (OpenAI SDK)
- `OpenAI(api_key=..., base_url=...)`.
- Gọi `audio.transcriptions.create(model=..., file=(filename, BytesIO(audio_bytes), mime), language=..., response_format=...)`.
- MIME map: `.wav` → `audio/wav`, `.mp3` → `audio/mpeg`.
- Trả về `str` đã strip; lỗi gateway → exception có message rõ (log correlation_id ở tầng route).
- **Không** tự viết multipart `httpx` trừ khi SDK không tương thích sau spike — ưu tiên SDK đồng bộ với LLM stack.

### 1.6 `app/stt/factory.py`
```python
def build_stt_client(
    stt: SttSettings,
    llm: LlmSettings,
) -> SttClient | None:
    """None nếu STT tắt hoặc thiếu api_key/base_url sau inherit."""
```

### 1.7 `scripts/fpt_whisper_transcribe_example.py`
CLI: `STT_API_KEY` / `LLM_API_KEY`, file `speech.wav`, in transcript — dùng trước khi nối FastAPI.

---

## Phase 2: Backend API — Transcribe Endpoint

### 2.1 `app/api/schemas.py`
```python
class TranscribeResponse(BaseModel):
    correlation_id: str
    transcript: str
    language: str | None = None
    error: ErrorObject | None = None
```

(`language_detected` / `duration_seconds` chỉ thêm khi gateway trả `verbose_json` — phase 1 không bắt buộc.)

### 2.2 `app/api/routes.py`
```python
@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    correlation_id: str = Header(alias="X-Correlation-Id"),
    claims: dict = Depends(_validate_auth),
) -> TranscribeResponse:
```

- Validate: `stt_enabled`, size ≤ `stt_max_upload_bytes`, extension/mime `wav` | `mpeg` | `webm` (hoặc chỉ `wav` sau FE convert).
- `language` form override `stt_language`.
- STT client `None` → HTTP 503 + message tiếng Việt.

### 2.3 `app/api/runtime.py`
Thêm vào `GraphRuntime` (hoặc service STT inject riêng, không qua LangGraph):
```python
def transcribe_audio(
    self,
    audio_bytes: bytes,
    *,
    filename: str,
    language: str | None,
    correlation_id: str,
) -> dict[str, Any]:
    ...
```

Transcribe **không** chạy graph — chỉ STT rồi trả JSON.

---

## Phase 3: Spring Relay — Audio Forwarding

### 3.1 `AiChatRelayController.java` — endpoint relay
`POST /api/v1/ai/chat/transcribe`:
1. Nhận `multipart/form-data` từ FE (JWT).
2. Forward file + `language` + `X-Correlation-Id` + `Authorization` tới Python.
3. Trả JSON `TranscribeResponse`.

**FE → Spring:**
```
POST /api/v1/ai/chat/transcribe
Content-Type: multipart/form-data
Authorization: Bearer <token>
X-Correlation-Id: <uuid>

file: recording.wav
language: vi (optional)
```

**Spring → Python:**
```
POST {pythonBaseUrl}/api/v1/ai/chat/transcribe
(same multipart + headers)
```

Dùng `HttpClient` multipart (tương tự pattern relay SSE hiện có, đổi body sang `multipart`).

---

## Phase 4: Frontend — Voice Recording UI

### 4.1 `ChatBotPage.tsx` — thay stub (dòng ~222–229)

**Hiện tại:** toggle gửi text cứng `"Nhập kho 50 thùng sữa..."`.

**Mới:** `MediaRecorder` → blob `webm` → `convertToWav` → `transcribeAudio` → `handleSend(transcript, "voice", ...)`.

### 4.2 `features/ai/utils/audioUtils.ts`
`convertToWav(blob: Blob): Promise<Blob>` — `AudioContext` + PCM16 WAV header.

### 4.3 `features/ai/api/aiChatSse.ts` — `transcribeAudio(wavBlob, { language?: "vi" })`
FormData `file` + `language`; header `Authorization`, `X-Correlation-Id`.

### 4.4 Luồng sau transcribe
```typescript
const { transcript } = await transcribeAudio(wavBlob);
if (!transcript?.trim()) { /* empty transcript */ return; }
handleSend(transcript, "voice", { voiceUrl: URL.createObjectURL(wavBlob) });
```

`types.ts` đã có `type: "voice"` và `voiceUrl?` — không đổi schema message.

---

## Phase 5: Validation & Error Handling

### 5.1 Backend
- Max size: `stt_max_upload_bytes` (10 MB).
- Max duration: ước lượng từ size hoặc validate sau decode (phase 2); giới hạn cấu hình `stt_max_audio_seconds`.
- Format ưu tiên: **WAV** từ FE; backend từ chối mime lạ với message rõ.
- STT down / chưa cấu hình → 503; không crash app khi `stt_enabled=false`.

### 5.2 Frontend — thông báo (tiếng Việt)
| Lỗi | Message |
|-----|---------|
| Không có quyền mic | "Vui lòng cấp quyền truy cập microphone để sử dụng tính năng ghi âm." |
| STT không khả dụng | "Dịch vụ chuyển giọng thành văn bản tạm thời không khả dụng." |
| Ghi quá dài | "Ghi âm quá dài (tối đa 60 giây)." |
| Transcript rỗng | "Không thể nhận diện giọng nói. Vui lòng thử lại." |
| Mạng | "Lỗi kết nối khi gửi ghi âm." |

### 5.3 UI khi đang transcribe
- Spinner trên nút mic; disable gửi text.
- Text: "Đang chuyển giọng thành văn bản..."

---

## Phase 6: Testing

### 6.1 Backend
- Unit test `FptWhisperClient` với mock `OpenAI` / patch `transcriptions.create`.
- Test factory: inherit `LLM_API_KEY`, disabled khi thiếu key.
- Test route: file quá lớn, STT disabled, transcript rỗng.

### 6.2 Frontend
- Mock `transcribeAudio`; flow start/stop recording.
- Error states (permission, 503, empty transcript).

### 6.3 Integration
- Record → transcribe → `handleSend` → chat stream (tiếng Việt).
- Smoke script: `python scripts/fpt_whisper_transcribe_example.py` với file WAV thật.

---

## Files to Create

| File | Purpose |
|------|---------|
| `ai_python/app/stt/__init__.py` | Exports |
| `ai_python/app/stt/protocol.py` | `SttClient` |
| `ai_python/app/stt/fpt_whisper.py` | FPT Whisper via OpenAI SDK |
| `ai_python/app/stt/factory.py` | `build_stt_client()` |
| `ai_python/scripts/fpt_whisper_transcribe_example.py` | Smoke / dev |
| `frontend/mini-erp/src/features/ai/utils/audioUtils.ts` | webm → WAV |

## Files to Modify

| File | Changes |
|------|---------|
| `ai_python/app/config/settings.py` | `SttSettings` + load helper |
| `ai_python/requirements.txt` | `openai` pin |
| `ai_python/.env.example` | Block `STT_*` |
| `ai_python/app/api/schemas.py` | `TranscribeResponse` |
| `ai_python/app/api/routes.py` | `POST /transcribe` |
| `ai_python/app/api/runtime.py` | Wire STT client |
| `backend/.../AiChatRelayController.java` | Relay transcribe |
| `frontend/.../ChatBotPage.tsx` | Recording thật |
| `frontend/.../aiChatSse.ts` | `transcribeAudio()` |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| FPT Whisper + OpenAI SDK | Cùng host/key với Gemma; đã có mẫu `fpt_openai_stream_example.py` |
| `SttSettings` tách `LlmSettings` | Model/timeout/language khác chat; vẫn inherit URL/key |
| Endpoint transcribe riêng | Không nhét base64 vào JSON chat; dễ test và relay multipart |
| FE → WAV | Codec browser không đồng nhất; backend nhận format ổn định |
| `language=vi` mặc định | Phù hợp nghiệp vụ ERP |
| STT ngoài LangGraph | Transcribe không cần graph state |

---

## Environment Variables

```env
# STT — optional; tắt nếu STT_ENABLED=0 hoặc thiếu key sau inherit
STT_ENABLED=1
STT_BASE_URL=                    # empty → LLM_BASE_URL (https://mkp-api.fptcloud.com)
STT_API_KEY=                     # empty → LLM_API_KEY
STT_MODEL=FPT.AI-whisper-medium
STT_LANGUAGE=vi
STT_RESPONSE_FORMAT=json
STT_MAX_AUDIO_SECONDS=60
STT_MAX_UPLOAD_BYTES=10485760
STT_HTTP_TIMEOUT_SECONDS=45

# LLM (đã có — STT có thể dùng chung)
LLM_BASE_URL=https://mkp-api.fptcloud.com
LLM_API_KEY=...
```

---

## Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Độ trễ Whisper | UI loading; `stt_http_timeout_seconds`; không block SSE chat |
| File lớn | Giới hạn 60s / 10MB FE + BE |
| Mic bị từ chối | Message rõ; vẫn nhập text |
| Gateway STT lỗi | 503; ẩn/disable nút mic khi `stt_enabled=false` |
| Chất lượng tiếng Việt | `language=vi`; hướng dẫn nói rõ, gần mic |
| SDK `file=` sai kiểu | Tuple `(name, stream, mime)` trong implementation |

---

## Out of Scope (tương lai)
- Lưu/play lại audio trên server (MediaAudits `Voice_Audio`)
- Streaming STT realtime (WebSocket)
- Auto-detect ngôn ngữ
- Local Whisper offline
