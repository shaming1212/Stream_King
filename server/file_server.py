import os
import time
import shutil
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, quote

logger = logging.getLogger("file_server")

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_files")
os.makedirs(TEMP_DIR, exist_ok=True)

_FILE_SERVER_PORT = 8766


class _FileHandler(BaseHTTPRequestHandler):
    """Serves a single file at GET /api/download/<filename>"""

    def log_message(self, fmt, *args):
        logger.info(fmt, *args)

    def do_GET(self):
        if not self.path.startswith("/api/download/"):
            self.send_error(404)
            return

        filename = unquote(self.path[len("/api/download/"):])
        filepath = os.path.join(TEMP_DIR, filename)

        if not os.path.isfile(filepath):
            self.send_error(404, "File not found")
            return

        try:
            size = os.path.getsize(filepath)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            encoded_name = quote(filename)
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{encoded_name}")
            self.send_header("Content-Length", str(size))
            self.end_headers()

            with open(filepath, "rb") as f:
                shutil.copyfileobj(f, self.wfile)

            logger.info("file served: %s (%d bytes)", filename, size)
        except Exception as e:
            logger.error("file serve error: %s", e)


class FileServer:
    """On-demand HTTP file server. Starts when a file is sent, stops after download."""

    def __init__(self):
        self._server = None
        self._thread = None
        self._stop_event = threading.Event()
        self.delivered = threading.Event()

    def start_with_file(self, filepath: str) -> str:
        """Copy file to temp dir, start HTTP server, return filename."""
        filename = os.path.basename(filepath)
        dest = os.path.join(TEMP_DIR, filename)
        # Avoid overwriting: add timestamp prefix if file already exists
        if os.path.exists(dest):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(time.time())}{ext}"
            dest = os.path.join(TEMP_DIR, filename)
        shutil.copy2(filepath, dest)

        if self._server is not None:
            self.stop()

        self._stop_event.clear()
        self.delivered.clear()
        self._server = HTTPServer(("0.0.0.0", _FILE_SERVER_PORT), _FileHandler)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("file server started on :%d for %s", _FILE_SERVER_PORT, filename)
        return filename

    def mark_delivered(self):
        """Called when mobile client confirms file received."""
        self.delivered.set()

    def _run(self):
        try:
            self._server.serve_forever()
        except Exception:
            pass

    def stop(self):
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
            try:
                self._server.server_close()
            except Exception:
                pass
            self._server = None
            logger.info("file server stopped")

    def cleanup(self):
        """Remove temp files."""
        self.stop()
        for f in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, f))
            except Exception:
                pass


file_server = FileServer()
