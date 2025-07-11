## Whatsanuker-POC – Mission Brief for the LLM Coding Agent

*A weekend-grade proof-of-concept that shows autonomous moderation, spam removal, and join-request vetting for a WhatsApp Community—all runnable on a single Mac.*

---

### 1. Why we’re doing this — background

1. **Pain**

   * Large WhatsApp Communities drown in join requests and spam.
   * Manual triage steals hours and still lets junk leak through.

2. **Opportunity**

   * Recent `whatsapp-web.js ≥ 1.31.1-alpha` exposes APIs to fetch/approve/reject membership requests and delete messages programmatically.
   * AWS Bedrock’s Claude-Sonnet-4 is accurate enough to classify short text with near-zero shot prompts.

3. **Goal of the POC**

   * **Prove** that a fully local, two-process bot can:

     1. Decide in real-time whether to approve/reject join requests.
     2. Delete spam messages and kick offending users.
     3. Log every decision so a human can audit it later.

---

### 2. Scope & non-scope

| **In**                                | **Out (defer to full product)**             |
| ------------------------------------- | ------------------------------------------- |
| Local Docker-Compose; no cloud deploy | Helm / ECS / K8s                            |
| Flat JSON logs on disk                | Redis, Loki, Prometheus, S3 backups         |
| One Community, one subgroup (“Lobby”) | Multi-group orchestration                   |
| Live Claude calls through **LiteLLM** | Caching, fine-tuned models, semantic search |
| Mac + Docker Desktop setup            | Windows, arm64 Pi                           |

---

### 3. High-level architecture

```
┌─────────────────────────┐      REST      ┌─────────────────────────┐
│  Node: wa-bridge        │◄──────────────►│  Python: llm-service    │
│  whatsapp-web.js        │                │  FastAPI + LiteLLM      │
│  (QR session)           │                │  ↳ AWS Bedrock Claude   │
└─────────────────────────┘                └─────────────────────────┘
      │  stdout JSON logs                             │
      └───────────────────────────────────────────────┘
```

*No external databases, no message queue—just two containers talking over localhost.*

---

### 4. Development & runtime constraints for the Agent

| Item                      | Hard rule                                                                 |
| ------------------------- | ------------------------------------------------------------------------- |
| **Language / runtimes**   | Node 18 (ES Modules) and Python 3.11                                      |
| **Dependencies**          | `whatsapp-web.js@^1.31.1-alpha`, `axios`, `fastapi`, `uvicorn`, `litellm` |
| **Model ID**              | `bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0`                      |
| **Environment variables** | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME=us-east-1` |
| **Storage**               | Logs only → `./logs/*.jsonl` (rotate daily, keep 7 days)                  |
| **No**                    | Redis, SQL, Prometheus, HTTPS, TLS offload                                |

---

### 5. File & folder layout to generate

```
whatsanuker-poc/
├─ bot/
│  ├─ index.js            # WA bridge
│  └─ Dockerfile
├─ llm/
│  ├─ main.py             # FastAPI app
│  ├─ policy.md           # Simple markdown rules (edit live)
│  └─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ docs/POC_RUN.md        # Setup & test script
```

---

### 6. Minimum viable features

| Flow              | Bot behaviour                                                                                                           | How to test                                                                                                 |                                                         |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Join-request**  | Poll every 45 s.<br>POST `/vet_join` → Claude → JSON \`approve                                                          | reject`.<br>Call `approveGroupMembershipRequests()`or`reject…()\` accordingly.<br>DM “Welcome!” on approve. | Use a second phone to request join with good/bad notes. |
| **Spam deletion** | `message_create` event → POST `/vet_message`.<br>If `is_spam: true` ⇒ `msg.delete(true)` + `chat.removeParticipants()`. | Send a link-spam message from test phone.                                                                   |                                                         |
| **Audit log**     | One line per action: `ts, type, contact, decision, reason, latency_ms`.                                                 | `jq '.decision' logs/*.jsonl` shows entries.                                                                |                                                         |
| **Self-healing**  | Docker `restart: on-failure` restarts either container; QR auth survives via mounted volume `./bot/.wwebjs_auth`.       | `docker kill llm` → container restarts automatically.                                                       |                                                         |

---

### 7. LiteLLM call patterns

```python
resp = litellm.completion(
    model=os.getenv("MODEL_ID"),
    messages=[
        {"role": "system","content": prompt_sys},
        {"role": "user",  "content": prompt_user}
    ],
    temperature=0.0,
    max_tokens=120
)
```

Guidelines:

* Always request **JSON-only** answers (`{"decision":"…","reason":"…"}`) to avoid parsing errors.
* On parse failure → default to *reject* (join) or *keep* (message) and log `"fallback":true`.

---

### 8. Policy template (`llm/policy.md`)

```md
### Admission
- Name contains at least 2 words.
- Note must mention "Agentics", "NYC", or "video".

### Messages
- Remove if:
  * Contains suspicious TLD (.tk, .ru, .click, .ly) OR
  * >70 % uppercase OR emoji with <5 words text OR
  * Begins with "Forwarded many times".
```

*Editable in-place; service reloads file each request.*

---

### 9. Local run instructions for end-user (Mac)

```bash
brew install docker
git clone https://github.com/<your fork>/whatsanuker-poc
cd whatsanuker-poc
cp .env.example .env      # fill AWS keys
docker compose up --build
# Scan the QR code that appears
```

Stop & wipe:

```bash
docker compose down -v
rm -rf bot/.wwebjs_auth logs/
```

---

### 10. Acceptance checklist for the Coding Agent

1. **Repo compiles**: `docker compose build` exits 0.
2. **Unit tests**: `pytest llm/tests` & `node --test bot/tests` green.
3. **Happy-path demo**: All four flows in §6 pass on maintainer’s MacBook.
4. **Docs**: `docs/POC_RUN.md` covers setup, env vars, and test script.
5. **Security sanity**: No credentials in git; calls Bedrock only via LiteLLM.

---

### End of briefing

Deliver the repo exactly as outlined, pass the checklist, and the POC is a wrap.
