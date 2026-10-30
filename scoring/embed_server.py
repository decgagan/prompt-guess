"""Local stand-in for Workers AI during `wrangler pages dev`: POST {"texts": [...]} -> {"vectors": [...]}.

python scoring/embed_server.py   # listens on 127.0.0.1:8789
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        texts = json.loads(self.rfile.read(int(self.headers["content-length"])))["texts"]
        vecs = MODEL.encode(texts, normalize_embeddings=True).tolist()
        body = json.dumps({"vectors": vecs}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("embed server on http://127.0.0.1:8789")
    ThreadingHTTPServer(("127.0.0.1", 8789), H).serve_forever()
