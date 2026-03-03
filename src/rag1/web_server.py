import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .query_data import query_rag
from .settings import LOG_LEVEL

logger = logging.getLogger(__name__)

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            path = "/index.html"

        if path.startswith("/api/"):
            self._send_json(404, {"error": "Not found"})
            return

        file_path = os.path.normpath(os.path.join(WEB_DIR, path.lstrip("/")))
        if not file_path.startswith(WEB_DIR):
            self._send(403, b"Forbidden", "text/plain; charset=utf-8")
            return

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return

        if file_path.endswith(".html"):
            ctype = "text/html; charset=utf-8"
        elif file_path.endswith(".css"):
            ctype = "text/css; charset=utf-8"
        elif file_path.endswith(".js"):
            ctype = "application/javascript; charset=utf-8"
        else:
            ctype = "application/octet-stream"

        with open(file_path, "rb") as f:
            body = f.read()
        self._send(200, body, ctype)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/query":
            self._send_json(404, {"error": "Not found"})
            return

        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len) if content_len > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        query = (payload.get("query") or "").strip()
        if not query:
            self._send_json(400, {"error": "Missing query"})
            return

        try:
            answer, sources = query_rag(query, return_sources=True)
        except TypeError:
            # Backwards compatibility if return_sources isn't supported
            answer = query_rag(query)
            sources = []
        except Exception as exc:
            logger.exception("Query failed")
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(200, {"answer": answer, "sources": sources})


def main():
    logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(name)s: %(message)s")
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), Handler)
    logger.info("Server running at http://%s:%s", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
