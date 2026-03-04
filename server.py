"""
Ethos Aegis — REST Server
FastAPI-free, stdlib-only HTTP server for the adjudication pipeline.

Usage:
    python server.py               # port 8080
    python server.py --port 9000
    AEGIS_PORT=9000 python server.py

Docker:
    CMD ["python", "server.py"]

Endpoints:
    POST /v1/adjudicate   — adjudicate a payload
    GET  /v1/health       — liveness check
    GET  /v1/codex        — pipeline statistics
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock

# ── Import pipeline ────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from ethos_aegis import EthosAegis
from ethos_aegis.vitality.protocol import AegisVitality

logging.basicConfig(
    level=os.getenv("AEGIS_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("aegis.server")

# ── Globals (process-scoped, thread-safe via Lock) ─────────────────────────
_LOCK    = Lock()
_AEGIS:  EthosAegis | None    = None
_VITAL:  AegisVitality | None = None
_API_KEY = os.getenv("AEGIS_API_KEY", "")

def _get_pipeline() -> tuple[EthosAegis, AegisVitality]:
    global _AEGIS, _VITAL
    if _AEGIS is None:
        with _LOCK:
            if _AEGIS is None:
                log.info("Initializing Ethos Aegis pipeline…")
                _AEGIS = EthosAegis()
                _VITAL = AegisVitality(_AEGIS)
                _VITAL.nourish()
                log.info("Pipeline online.")
    return _AEGIS, _VITAL  # type: ignore


# ── HTTP Handler ───────────────────────────────────────────────────────────

class AegisHandler(BaseHTTPRequestHandler):
    server_version = "EthosAegis/1.0"

    # ── Auth ──────────────────────────────────────────────────────────────
    def _check_auth(self) -> bool:
        if not _API_KEY:
            return True
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {_API_KEY}"

    # ── Response helpers ──────────────────────────────────────────────────
    def _send_json(self, code: int, data: dict) -> None:
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Powered-By", "EthosAegis")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    # ── Routes ────────────────────────────────────────────────────────────
    def do_GET(self) -> None:
        if self.path == "/v1/health":
            self._send_json(200, {"status": "ok", "timestamp": time.time()})
        elif self.path == "/v1/codex":
            aegis, _ = _get_pipeline()
            self._send_json(200, aegis.codex())
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/adjudicate":
            self._send_json(404, {"error": "Not found"})
            return

        if not self._check_auth():
            self._send_json(401, {"error": "Unauthorized"})
            return

        try:
            body    = self._read_body()
            payload = body.get("payload", "")
            context = body.get("context", {})
            req_id  = body.get("request_id", "")
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        if not payload:
            self._send_json(400, {"error": "payload field is required"})
            return

        try:
            aegis, _ = _get_pipeline()
            t0 = time.perf_counter()
            verdict = aegis.adjudicate(payload, context=context)
            ms = (time.perf_counter() - t0) * 1000

            self._send_json(200, {
                "sanctified":   verdict.is_sanctified,
                "condemned":    verdict.is_condemned,
                "depth":        verdict.sovereignty_depth.name,
                "malignaCount": len(verdict.maligna_found),
                "sanitized":    verdict.purified_payload is not None,
                "report":       verdict.axiological_report,
                "latencyMs":    round(ms, 2),
                "requestId":    req_id,
            })
        except Exception as e:
            log.error("Adjudication error: %s\n%s", e, traceback.format_exc())
            self._send_json(500, {"error": "Internal server error"})

    def log_message(self, fmt, *args):  # suppress default access log noise
        log.debug(fmt % args)


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ethos Aegis REST Server")
    parser.add_argument("--port",    type=int, default=int(os.getenv("AEGIS_PORT", 8080)))
    parser.add_argument("--host",    type=str, default=os.getenv("AEGIS_HOST", "0.0.0.0"))
    parser.add_argument("--workers", type=int, default=1,
                        help="Reserved — stdlib HTTPServer is single-threaded. Use gunicorn for multi-worker.")
    args = parser.parse_args()

    # Warm up pipeline before accepting connections
    _get_pipeline()

    server = HTTPServer((args.host, args.port), AegisHandler)
    log.info("Ethos Aegis REST server listening on %s:%d", args.host, args.port)
    log.info("POST /v1/adjudicate  |  GET /v1/health  |  GET /v1/codex")
    if _API_KEY:
        log.info("API key authentication: ENABLED")
    else:
        log.warning("AEGIS_API_KEY not set — server is unauthenticated")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
