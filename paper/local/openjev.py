"""Serve open-jev-deberta-v3-large in the wire format, so the engine reaches it like any provider.

    python local/openjev.py --port 8103      # then PROVIDER=openjev

The model ships its own loader (typed_decisions/ in the Hugging Face snapshot); it has no server.
Its options are plain strings, so a choice option is its criteria description (the key when there
is none) and a score level is its criteria text. Structured states are sent as JSON, as to OpenAI.
"""

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from huggingface_hub import snapshot_download

REPO = "com-kotobalabs/open-jev-deberta-v3-large"


def text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


class Server:
    def __init__(self, repo=REPO):
        path = snapshot_download(repo)
        sys.path.insert(0, path)
        from typed_decisions.open_jev import OpenJev
        self.model, self.lock = OpenJev.from_pretrained(path, device="cpu"), threading.Lock()

    def answer(self, state, questions: dict) -> dict:
        asked, keys = [], []
        for q in questions.values():
            criteria = q.get("criteria") or {}
            if q["type"] == "choice":
                keys.append(list(criteria))
                options = [text(d if d is not None else k) for k, d in criteria.items()]
            elif q["type"] == "score":
                keys.append([str(i) for i in range(len(criteria))])
                options = [text(level) for level in criteria]
            else:
                keys.append(None)
                options = None
            asked.append({"type": q["type"], "instructions": text(q.get("instructions") or ""), "options": options})
        with self.lock:
            raw = self.model.decide(text(state), asked)
        answers = {}
        for qid, q, k, a in zip(questions, questions.values(), keys, raw):
            if q["type"] == "noul":
                answers[qid] = {"type": "noul", "noul": a["noul"]}
                continue
            probabilities = dict(zip(k, a["probabilities"].values()))
            answers[qid] = {"type": q["type"], q["type"]: k[list(a["probabilities"]).index(a["choice"])] if q["type"] == "choice" else a["score"],
                            "confidence": a["confidence"], "probabilities": probabilities}
        return answers


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8103)
    args = parser.parse_args()
    server = Server()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            try:
                out, status = {"model": "open-jev-deberta-v3-large", "answers": server.answer(body["state"], body["questions"])}, 200
            except (KeyError, ValueError) as err:
                out, status = {"error": str(err)}, 422
            data = json.dumps(out).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    print(f"open-jev on http://{args.host}:{args.port}/v1/systemone", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
