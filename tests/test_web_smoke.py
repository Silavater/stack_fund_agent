"""Web app smoke — the offline GET/HEAD routes boot and return 200 (no Docker, no network).

Exercises the static rendering of the pricing / chat-gate / desk / finops / journal
surfaces. The LLM chat (`/api/chat`) needs the agent container and is not covered here.
"""

import http.server
import sys
import threading
import urllib.request
from importlib import import_module
from pathlib import Path

# ui/server.py is a plain script (no package) — make it importable for the test.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ui"))
server = import_module("server")


def _serve():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def test_offline_get_routes_return_200():
    httpd, port = _serve()
    try:
        for path in ("/healthz", "/pricing", "/desk", "/finops", "/journal"):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=15) as r:
                assert r.status == 200, f"{path} -> {r.status}"
    finally:
        httpd.shutdown()


def test_head_healthz_returns_200():
    httpd, port = _serve()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/healthz", method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200
    finally:
        httpd.shutdown()
