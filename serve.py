#!/usr/bin/env python3
"""
Hoppd server — serves the app and persists user data.

Data is stored in a GitHub Gist (Render's free tier has no persistent disk, so a
Gist is used as the storage layer). If no Gist is configured it falls back to a
local file, which is fine for local development but is ephemeral on Render.

Environment variables (set these in the Render dashboard):
  PORT          - provided automatically by Render
  GITHUB_TOKEN  - a GitHub token with the "gist" scope
  GIST_ID       - the id of the Gist that holds the data file
  GIST_FILE     - (optional) filename inside the Gist. Default: hoppd-data.json
  APP_DIR       - (optional) directory containing index.html. Default: this file's dir
"""
import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "10000"))
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GIST_ID = os.environ.get("GIST_ID", "").strip()
GIST_FILE = os.environ.get("GIST_FILE", "hoppd-data.json").strip()

try:
    APP_DIR = os.environ.get("APP_DIR") or os.path.dirname(os.path.abspath(__file__))
except Exception:
    APP_DIR = os.environ.get("APP_DIR", ".")

LOCAL_FILE = os.path.join(APP_DIR, "hoppd-data.local.json")
GIST_ON = bool(GITHUB_TOKEN and GIST_ID)


def _gh(method, url, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "token " + GITHUB_TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "hoppd-app")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode() or "{}")


def load_data():
    """Return the stored JSON as a string ('{}' if none)."""
    if GIST_ON:
        try:
            gist = _gh("GET", "https://api.github.com/gists/" + GIST_ID)
            f = (gist.get("files") or {}).get(GIST_FILE)
            if f and f.get("content"):
                return f["content"]
        except Exception as e:
            print("[hoppd] gist load failed:", e)
        return "{}"
    try:
        with open(LOCAL_FILE, "r", encoding="utf-8") as fp:
            return fp.read() or "{}"
    except FileNotFoundError:
        return "{}"


def save_data(content):
    """Validate + persist the JSON string."""
    json.loads(content)  # raises if the body isn't valid JSON
    if GIST_ON:
        _gh("PATCH", "https://api.github.com/gists/" + GIST_ID,
            {"files": {GIST_FILE: {"content": content}}})
        return
    with open(LOCAL_FILE, "w", encoding="utf-8") as fp:
        fp.write(content)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _file(self, name, ctype):
        try:
            with open(os.path.join(APP_DIR, name), "rb") as fp:
                self._send(200, fp.read(), ctype)
        except FileNotFoundError:
            self._send(404, b"not found", "text/plain")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._file("index.html", "text/html; charset=utf-8")
        if self.path == "/api/health":
            return self._send(200, json.dumps({"ok": True, "storage": "gist" if GIST_ON else "local"}).encode())
        if self.path == "/api/data":
            try:
                return self._send(200, load_data().encode())
            except Exception as e:
                return self._send(500, json.dumps({"error": str(e)}).encode())
        # allow serving any other static asset that lives next to index.html
        safe = self.path.lstrip("/").split("?")[0]
        if safe and "/" not in safe and ".." not in safe and os.path.isfile(os.path.join(APP_DIR, safe)):
            ext = safe.rsplit(".", 1)[-1].lower()
            ctype = {"css": "text/css", "js": "application/javascript",
                     "png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml",
                     "ico": "image/x-icon", "json": "application/json"}.get(ext, "application/octet-stream")
            return self._file(safe, ctype)
        return self._send(404, b"not found", "text/plain")

    def do_PUT(self):
        if self.path != "/api/data":
            return self._send(404, b"not found", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            save_data(body)
            return self._send(200, json.dumps({"ok": True}).encode())
        except json.JSONDecodeError:
            return self._send(400, json.dumps({"error": "invalid JSON"}).encode())
        except Exception as e:
            print("[hoppd] save failed:", e)
            return self._send(500, json.dumps({"error": str(e)}).encode())

    def log_message(self, *args):
        pass  # keep Render logs quiet


if __name__ == "__main__":
    print("[hoppd] serving %s on 0.0.0.0:%d  (storage: %s)"
          % (APP_DIR, PORT, "GitHub Gist" if GIST_ON else "local file"))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
