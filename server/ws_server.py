import asyncio
import json
import logging
import websockets
import threading

from core.config import WS_HOST, WS_PORT

logger = logging.getLogger("ws_server")


class WebSocketServer:
    def __init__(self):
        self.clients = set()
        self.loop = None
        self._server = None
        self._stop = asyncio.Event()

    async def _handle(self, ws):
        self.clients.add(ws)
        logger.info("client connected (%d)", len(self.clients))
        try:
            async for msg in ws:
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(ws)
            logger.info("client disconnected (%d)", len(self.clients))

    async def _run(self):
        self.loop = asyncio.get_running_loop()
        self._server = await websockets.serve(self._handle, WS_HOST, WS_PORT)
        logger.info("ws server started on ws://%s:%d", WS_HOST, WS_PORT)
        await self._stop.wait()
        self._server.close()
        await self._server.wait_closed()
        logger.info("ws server closed")

    def start(self):
        threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    def stop(self):
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self._stop.set)

    def _send(self, client, payload: str):
        try:
            asyncio.run_coroutine_threadsafe(client.send(payload), self.loop)
        except Exception:
            logger.debug("send failed", exc_info=True)
            self.clients.discard(client)

    def broadcast_text(self, text: str):
        if not self.clients or not self.loop:
            return
        payload = json.dumps({"action": "insert_text", "text": text})
        for c in list(self.clients):
            self._send(c, payload)
        logger.info("broadcast text to %d clients: %s", len(self.clients), text)

    def broadcast_image(self, b64: str):
        if not self.clients or not self.loop:
            return
        payload = json.dumps({"action": "upload_image", "data": b64})
        for c in list(self.clients):
            self._send(c, payload)
        logger.info("broadcast image to %d clients", len(self.clients))


ws_manager = WebSocketServer()
