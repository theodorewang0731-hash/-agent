#!/usr/bin/env python3
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, api_base: str, **kwargs):
        self.api_base = api_base
        self.root_directory = Path(directory)
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/config.js":
            body = f"window.REGENTOS_CONFIG = {{ apiBase: '{self.api_base}' }};".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        target = self.root_directory / parsed.path.lstrip("/")
        if parsed.path not in ("/", "") and target.exists() and target.is_file():
            super().do_GET()
            return
        self.path = "/index.html"
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve RegentOS dashboard prototype")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7891)
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    dist_dir = Path(__file__).parent / "dist"
    static_dir = dist_dir if dist_dir.exists() else Path(__file__).parent / "static"
    handler = partial(DashboardHandler, directory=str(static_dir), api_base=args.api_base)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Dashboard running at http://{args.host}:{args.port}")
    print(f"API base: {args.api_base}")
    print(f"Serving from: {static_dir}")
    server.serve_forever()


if __name__ == "__main__":
    main()
