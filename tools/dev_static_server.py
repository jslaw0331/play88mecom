#!/usr/bin/env python3
"""
Serve the static mirror and proxy WordPress admin-ajax to production.

Ajax Search Pro uses POST /wp-admin/admin-ajax.php. A static mirror has no PHP.
Pointing the browser at the live AJAX URL triggers CORS; proxy keeps same-origin.

  python tools/dev_static_server.py
  Open http://127.0.0.1:8765/

Optional: python tools/dev_static_server.py --port 5500 --upstream https://www.play88m.com
"""

from __future__ import annotations

import argparse
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


def normalize_admin_path(raw_path: str) -> str:
    path_only = urllib.parse.unquote(raw_path.split("?", 1)[0])
    p = urllib.parse.urlsplit(path_only).path.replace("//", "/")
    return p.rstrip("/") or "/"


def handler_factory(repo_root: str, upstream_origin: str):
    origin = upstream_origin.rstrip("/")
    ajax_url = f"{origin}/wp-admin/admin-ajax.php"
    post_url = f"{origin}/wp-admin/admin-post.php"

    class MirrorHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=repo_root, **kwargs)

        def should_proxy_path(self) -> bool:
            n = normalize_admin_path(self.path)
            return n == "/wp-admin/admin-ajax.php" or n == "/wp-admin/admin-post.php"

        def _collect_upstream_headers(self) -> dict[str, str]:
            h: dict[str, str] = {}
            ua = self.headers.get("User-Agent") or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            h["User-Agent"] = ua
            forward = ["Accept", "Accept-Language", "Content-Type", "Referer", "Cookie", "Origin"]
            for name in forward:
                v = self.headers.get(name)
                if not v:
                    v = self.headers.get(name.lower())
                if v:
                    h[name] = v
            return h

        def proxy_to(self, url: str) -> None:
            body = b""
            if self.command in {"POST", "PUT", "PATCH"}:
                req_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(req_len) if req_len > 0 else b""

            req_headers = self._collect_upstream_headers()
            up_req = urllib.request.Request(url, data=body if body else None, method=self.command)
            for k, val in req_headers.items():
                up_req.add_header(k, val)

            try:
                with urllib.request.urlopen(up_req, timeout=90) as resp:
                    payload = resp.read()
                    status = getattr(resp, "status", resp.getcode())
                    self.send_response(status)
                    for k, val in resp.headers.items():
                        lk = k.lower()
                        if lk in HOP_BY_HOP or lk == "date":
                            continue
                        self.send_header(k, val)
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
            except urllib.error.HTTPError as exc:
                err_body = exc.read()
                self.send_response(exc.code)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body if err_body else b"")
            except OSError:
                msg = b"Upstream request failed.\n"
                self.send_response(HTTPStatus.BAD_GATEWAY)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)

        def do_GET(self) -> None:
            if self.should_proxy_path():
                q = ""
                if "?" in self.path:
                    q = "?" + self.path.split("?", 1)[1]
                decoded = urllib.parse.unquote(self.path.split("?", 1)[0])
                path = urllib.parse.urlsplit(decoded).path.rstrip("/")
                if path.endswith("/admin-post.php"):
                    self.proxy_to(post_url + q)
                else:
                    self.proxy_to(ajax_url + q)
            else:
                super().do_GET()

        def do_POST(self) -> None:
            if self.should_proxy_path():
                decoded = urllib.parse.unquote(self.path.split("?", 1)[0])
                path = urllib.parse.urlsplit(decoded).path.rstrip("/")
                q = ""
                if "?" in self.path:
                    q = "?" + self.path.split("?", 1)[1]
                if path.endswith("/admin-post.php"):
                    self.proxy_to(post_url + q)
                else:
                    self.proxy_to(ajax_url + q)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "No resource for POST")

        def do_OPTIONS(self) -> None:
            if self.should_proxy_path():
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()
            else:
                super().send_error(HTTPStatus.METHOD_NOT_ALLOWED)

    return MirrorHandler


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Static mirror + admin-ajax proxy")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--upstream", default="https://www.play88m.com")
    ns = parser.parse_args()

    handler = handler_factory(str(root), ns.upstream)
    httpd = ThreadingHTTPServer((ns.host, ns.port), handler)
    up = ns.upstream.rstrip("/")
    print(f"Serving {root} at http://{ns.host}:{ns.port}/")
    print(f"Proxy {up}/wp-admin/admin-ajax.php (and admin-post.php)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
