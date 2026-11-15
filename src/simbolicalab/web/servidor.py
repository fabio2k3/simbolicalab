"""Servidor local sin dependencias: sirve la interfaz y expone la API. Uso: python -m simbolicalab.web"""
from __future__ import annotations

import json, math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .api import API

ESTATICO = Path(__file__).parent / "static"


def _limpio(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {str(k): _limpio(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_limpio(v) for v in x]
    return x


class Manejador(BaseHTTPRequestHandler):
    def _enviar(self, codigo, cuerpo: bytes, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        self._enviar(200, (ESTATICO / "index.html").read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        nombre = self.path.removeprefix("/api/")
        if nombre not in API:
            return self._enviar(404, b'{"error":"no existe"}', "application/json")
        try:
            largo = int(self.headers.get("Content-Length", 0))
            params = json.loads(self.rfile.read(largo) or b"{}")
            cuerpo = json.dumps(_limpio(API[nombre](params)), ensure_ascii=False).encode()
            self._enviar(200, cuerpo, "application/json; charset=utf-8")
        except Exception as e:  # el error llega a la interfaz en vez de perderse en la consola
            self._enviar(400, json.dumps({"error": f"{type(e).__name__}: {e}"}).encode(), "application/json")

    def log_message(self, *a):
        pass


def servir(puerto: int = 8000):
    print(f"SimbólicaLab en http://127.0.0.1:{puerto}  (Ctrl+C para salir)")
    ThreadingHTTPServer(("127.0.0.1", puerto), Manejador).serve_forever()
