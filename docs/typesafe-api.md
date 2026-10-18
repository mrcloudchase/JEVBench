# Jev (TypeSafe AI) — research notes

Verified live against `https://api.typesafe.ai` on 2026-10-17 using `TYPESAFE_API_KEY` from the environment.

## What it is

Jev is TypeSafe AI's "System One" model. It is a decision model, not a text generator. You send it
a `state` (string, object, or array) plus a map of typed `questions`, and it returns one typed,
probabilistic answer per question in a single round trip. It is non-autoregressive, so all questions
are evaluated in parallel and latency is ~0.2–0.5 s regardless of question count.

- Input tokens only are billed: $0.042 per million. Output is free.
- Context: 64k tokens per request, 32k per question (262k with `TypeSafe-Danger-Zone-Long-Context: true`).
- Models: `jev-1.13.0` (alias `jev-latest`), `jev-1.14.0` (alias `jev-preview`, released 2026-10-14).
- Images: PNG/JPEG, 280–1568 px per side, need header `TypeSafe-Danger-Zone-Images: true`.
- Box questions need Jev 1.14.

## Wire format

`POST https://api.typesafe.ai/v1/systemone`
Headers: `Authorization: Bearer <key>`, `Content-Type: application/json`

```json
{
  "model": "jev-latest",
  "state": "<string | object | array>",
  "questions": {
    "<your_id>": { "type": "noul" | "choice" | "score" | "box", "instructions": "...", "criteria": ... }
  },
  "assets": { "<ref>": { "type": "image", "format": "png", "data_base64": "..." } }
}
```

`assets` is optional. Question IDs are yours; the model never sees them, and answers come back under
the same keys. `instructions` and every `criteria` value may be a string, object, or array.

| Type | Request fields | Answer fields |
|---|---|---|
| `noul` | `instructions`; optional `criteria: {"true": ..., "false": ...}` | `noul` (0–1, P(yes)). No `confidence`. |
| `choice` | `instructions`; `criteria: {option: description \| null}` (≤255 options) | `choice`, `probabilities` (sum to 1), `confidence` |
| `score` | `instructions`; `criteria: [level0, level1, ...]` (2–10 ordered levels) | `score` (expected value Σ i·pᵢ), `legend`, `probabilities` (keyed "0".."n-1"), `confidence` |
| `box` | `instructions` referencing an image asset; no criteria; Jev 1.14 only | `box: {top, bottom, left, right}` (0–1 fractions), `confidence` |

Response envelope:

```json
{ "model": "jev-1.13.0", "answers": { "<id>": { "type": "...", ... } }, "usage": { "input_tokens": N, "output_tokens": N } }
```

Errors: `{"detail": {"error_type": "api_usage_error", "message": "Invalid request."}}` with HTTP 400/401/413/415/422/429/529.

Confidence:
- choice: `(p_max − 1/n) / (1 − 1/n)`. Only the top probability matters.
- score: `max(0, 1 − Σ pᵢ·|i − m| / MAD_unif)`. Distance-aware, mass on neighbouring levels costs less.

Images: put a reference string in `state`/`instructions`/`criteria`, and define it in `assets`.
Either base64 JSON (`data_base64` + `format`) or multipart (`-F request=<json>` + `-F <part>=@file`, asset has `"part": "<name>"`).

## SDKs

- Python: `pip install typesafe-sdk` → `TypeSafeClient(model=...).system_one(state=, questions={id: Choice(...)|Score(...)|Noul(...)})`
- JS/TS: `npm install @typesafe-ai/sdk` (tested v0.7.0) → `new TypeSafeClient({defaultModel}).systemOne({state, questions: {id: choice(instr, criteria) | score(instr, levels) | noul(instr)}})`
- Both return the raw wire response shape (`answers[id].choice` etc). SDKs retry 429/529 and zstd-compress bodies ≥1 KiB.
- Also available via Vercel AI Gateway (`typesafe-ai/jev`, `boolean` ≡ `noul`), OpenRouter Decisions API, Cloudflare, Promptfoo.

## Documented weaknesses (jev-1.13 "jaggedness" page)

Literal reading of instructions; unreliable counting and arithmetic; weak on numeric encodings (hex, binary);
score values only loosely calibrated between levels; dates treated as text; double negatives / multi-hop
reasoning; distracted by irrelevant state; no prompt-injection hardening; contradictory criteria;
bias toward the first choice option; cannot generate text.

## Live examples (`tests/fixtures/`)

- `example_request_text.json` → `example_response_text_jev-1.13.0.json`, `example_response_text_jev-1.14.0.json`
  (choice + score + 3× noul on a support ticket; 654 input tokens; 0.48 s and 0.21 s)
- `example_request_box.json` (on an image of shapes, not kept) → `example_response_box_jev-1.14.0.json`
  (2× box + choice + noul on an image; red rectangle located at 0.86 confidence,
  blue square misplaced at 0.26 confidence, so the confidence signal flagged the miss)

## Sources

- https://docs.typesafe.ai/api, /primitives/{choice,score,noul,box}, /images, /confidence, /models, /model-jaggedness/jev-1.13, /llms.txt
- https://en.wikipedia.org/wiki/Jev_(AI_model)
- https://vercel.com/changelog/ai-gateway-now-supports-typesafe-clients-and-http-api-for-jev
- https://www.promptfoo.dev/docs/providers/typesafe/
- https://dev.to/valyuai/how-to-use-jev-a-practical-guide-to-typesafes-system-one-model-g5e
