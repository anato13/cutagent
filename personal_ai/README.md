# ANATO12 AI

A small, private chat assistant for Windows. It uses your existing local Ollama installation and `qwen2.5:7b`. It runs a browser interface on **your own computer** at `http://127.0.0.1:8766`. No account or Python packages are required beyond Python itself.

## Set up on Windows

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/). During installation, select **Add Python to PATH**. If you already have Python, open Command Prompt and run `py -3 --version`.
2. Start Ollama. In Command Prompt, run `ollama list` and check that `qwen2.5:7b` appears. If it does not, run `ollama pull qwen2.5:7b` once. The model download needs internet; ordinary chat does not.
3. Keep the entire `personal_ai` folder together. Double-click `START_ANATO12_AI.bat`. Your browser should open ANATO12 AI. If it does not, visit `http://127.0.0.1:8766` while the Command Prompt window is open.
4. To stop the assistant, close the Command Prompt window. To use it again, double-click the launcher. Your chats and memories will still be there.

The first message can take a while while Ollama loads the model into memory. If another app already uses port 8766, close it before launching. If you see **Local Ollama is unavailable**, start Ollama and check `ollama list`.

The model menu lists other downloaded local Ollama models too. You can switch
between `qwen2.5:7b` and `qwen3:8b` without losing the conversation or approved
memories. When you switch, ANATO12 AI asks Ollama to release its previous model;
this helps limit RAM/VRAM use. Other Ollama applications manage their own models.

## How memory works

Use **Remember this** to copy text into the memory editor, review it, choose a type, and press **Save memory**. **Suggest memory** asks Ollama to extract one clearly stated preference from the current conversation. Its result stays **pending** until you review and approve it. The assistant only puts approved memories in its prompt. Memories survive restarts and are separate from conversation history. **Edit** corrects an outdated memory; **Forget** removes it. The chat reply reports how many approved memories were retrieved. The local API also returns the exact memory IDs used.

The right panel accepts text, Markdown, SRT, and VTT files up to 500 KB each. Matching excerpts from those files can be supplied to a future chat, but imports do **not** silently become personal memories. For an approved example transcript, press **Suggest humor note**; Ollama proposes a tentative observation that remains **pending** until you review and approve it. This first version reads at most the first 3,500 characters for this suggestion. The `This is funny`, `This isn't funny`, and `My editing style` memory types let you save observations from transcripts or clips you reviewed yourself. The feedback buttons record examples of good/bad/funny replies and optional notes for later prompts. This is retrieval and preference storage; it does **not** retrain Ollama model weights. Video and audio analysis, voice chat, and semantic search are future work. Large files and binary media cannot be imported in this version.

Use **Download backup** regularly. **Restore** replaces the current chats, memories, documents, and settings with the selected backup. Delete chats from the left panel and memories individually from the right panel. To erase **all** assistant data, close the app and delete `%LOCALAPPDATA%\Anato12AI`; that also changes the API key on next start. Your own backup files must be deleted separately.

The default data location is `%LOCALAPPDATA%\Anato12AI\memory.sqlite3`. Set `ANATO12_AI_DATA_DIR` before launching to choose another location. Backups are JSON files containing private content; keep them private. No chat/document data is sent to a cloud service by this application. Ollama is contacted only at `127.0.0.1:11434`, and remote-backed model entries are rejected. The API listens only on `127.0.0.1`, requires a random bearer token for data routes, and checks browser origin. The token is stored in `%LOCALAPPDATA%\Anato12AI\api-key` and is displayed only to the local page. This protects against casual cross-site or network access, but a malicious program running as you on your PC could read local files.

## For ANATO12 Studio integration

The existing Studio code is unchanged. A future Studio adapter can read the token from `%LOCALAPPDATA%\Anato12AI\api-key` and call the versioned local API while ANATO12 AI is running:

```http
GET http://127.0.0.1:8766/api/v1/integration/preferences
Authorization: Bearer <contents of api-key>
```

This returns confirmed humor and editing preferences with IDs and timestamps. For more context:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/v1/state` | GET | Conversations, memories, document names, personality |
| `/api/v1/conversations` | GET/POST | List or create chats; `?q=text` searches titles and messages |
| `/api/v1/conversations/{id}` | GET/DELETE | Read or delete a chat |
| `/api/v1/conversations/{id}/suggest-memory` | POST | Suggest a pending preference from recent dialogue |
| `/api/v1/chat` | POST | `{ "conversation": 1, "message": "...", "model": "qwen2.5:7b" }`; returns reply, retrieved memory/document IDs, and Ollama timing metrics when available |
| `/api/v1/memories` | POST | Save `{ "kind": "humor_like", "content": "...", "confirmed": true }` |
| `/api/v1/memories/{id}` | PUT/DELETE | Correct, approve, or forget a memory |
| `/api/v1/documents` | POST | Import `{ "title": "example.srt", "content": "..." }` |
| `/api/v1/documents/{id}/analyze` | POST | Suggest a pending humor observation from a transcript |
| `/api/v1/documents/{id}` | DELETE | Remove a document |
| `/api/v1/feedback` | POST | Save `{ "message": 12, "decision": "funny", "note": "..." }` |
| `/api/v1/personality` | PUT | Save `{ "text": "..." }` independently of memory |
| `/api/v1/backup` | GET | Export all assistant data as JSON |
| `/api/v1/restore` | POST | Replace data with a valid backup JSON |

The integration endpoint returns **notes**, not automatic humor rankings or trained weights. Studio now has an opt-in **Use Personal AI memory** checkbox. When enabled, its chat uses this local API for durable conversation and memory retrieval, and clip analysis receives up to four short confirmed humor/editing notes. Start ANATO12 AI before enabling it. Studio review decisions remain in Studio's separate database; future work can send specifically approved examples back with the user's control.

## Design choice and verification

We checked [Open WebUI](https://github.com/open-webui/open-webui). It advertises Ollama chat, history, memories, documents, and extensibility, and may be an excellent full interface later. It was not installed in this environment. This compact, dependency-free application keeps memory approval and the Studio API explicit, and avoids adding a second large service for the first working version. Open WebUI's individual memory behaviors were **not** tested here.

Run the automated tests with `py -3 -m unittest discover -s tests -v` from the `personal_ai` folder. These verify database persistence across a new Store instance, correction/retrieval, backup/restore, feedback, local API authentication, and chat search using a deterministic fake model. Real Ollama and native Windows startup are separate checks; see the delivery notes for their status.
