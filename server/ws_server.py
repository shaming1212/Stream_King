import asyncio
import json
import logging
import os
import time
import hashlib
import socket
import ssl
import threading

import websockets
from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

from core.config import APP_VERSION, WS_HOST, WS_PORT

_CERT_PATH = os.path.join(os.path.dirname(__file__), "cert.pem")
_KEY_PATH = os.path.join(os.path.dirname(__file__), "key.pem")

logger = logging.getLogger("aura.ws")


def _is_lan(ip: str) -> bool:
    return ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if _is_lan(ip):
            return ip
    except Exception:
        pass

    import ifaddr
    adapters = ifaddr.get_adapters()
    for adapter in adapters:
        for addr_obj in adapter.ips:
            if addr_obj.is_IPv4 and _is_lan(addr_obj.ip):
                return addr_obj.ip

    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


class WebSocketServer:
    def __init__(self):
        self.clients = set()
        self.client_meta = {}
        self.loop = None
        self._server = None
        self._stop = None
        self.on_mobile_audio = None
        self.on_mobile_image = None
        self.on_mobile_voice = None
        self.on_file_received = None
        self._recent_image_ids = {}
        self._recent_image_ttl = 300

    def _set_client_source(self, ws, source: str):
        if not source:
            return
        meta = self.client_meta.setdefault(ws, {})
        old = meta.get("source", "unknown")
        meta["source"] = source
        if old != source:
            logger.info("client source set: %s -> %s", old, source)

    def _get_client_source(self, ws) -> str:
        return self.client_meta.get(ws, {}).get("source", "unknown")

    def _normalize_image_id(self, msg_id, b64: str) -> str:
        if msg_id:
            return str(msg_id)
        digest = hashlib.sha1(f"{len(b64)}:{b64[:256]}:{b64[-256:]}".encode("utf-8")).hexdigest()
        return f"image_{digest}"

    def _is_duplicate_image(self, msg_id: str) -> bool:
        now = time.time()
        expired = [k for k, ts in self._recent_image_ids.items() if now - ts > self._recent_image_ttl]
        for k in expired:
            self._recent_image_ids.pop(k, None)
        if msg_id in self._recent_image_ids:
            return True
        self._recent_image_ids[msg_id] = now
        return False

    async def _handle(self, ws):
        self.clients.add(ws)
        self.client_meta[ws] = {"source": "unknown"}
        logger.info("client connected (%d)", len(self.clients))
        try:
            async for msg in ws:
                try:
                    data = json.loads(msg)
                    action = data.get("action")
                    source = data.get("source")
                    if source:
                        self._set_client_source(ws, source)

                    if action == "client_hello":
                        await ws.send(json.dumps({"action": "client_hello_ack", "ok": True}))

                    elif action == "ping":
                        await ws.send(json.dumps({"action": "pong"}))

                    elif action == "upload_image":
                        # Mobile sends screenshots here. Server ACK means only:
                        # "server received this image". Browser injection is a
                        # separate step and must not block the mobile upload queue.
                        self._set_client_source(ws, source or "mobile")
                        b64 = data.get("data", "")
                        msg_id = self._normalize_image_id(data.get("id"), b64)
                        ok = bool(b64)

                        await ws.send(json.dumps({
                            "action": "upload_image_ack",
                            "id": msg_id,
                            "ok": ok,
                        }))
                        logger.info("upload_image_ack sent id=%s ok=%s", msg_id, ok)

                        if not ok:
                            logger.warning("mobile image empty id=%s", msg_id)
                            continue

                        if self._is_duplicate_image(msg_id):
                            logger.info("duplicate upload_image ignored id=%s", msg_id)
                            continue

                        # Always forward to extension/non-mobile clients. Do not
                        # send the big image back to the mobile sender, otherwise
                        # the mobile websocket may receive its own image and churn.
                        self.broadcast_image(b64, msg_id=msg_id, exclude=ws)

                        # Do not call on_mobile_image here by default. Older GUI code
                        # may also broadcast images from that callback, which causes the
                        # same phone screenshot/photo to be injected twice in the web page.
                        # The single authoritative forwarding path is broadcast_image().
                        logger.info("mobile image received id=%s (%d chars); forwarded once", msg_id, len(b64))

                    elif action == "upload_audio":
                        self._set_client_source(ws, source or "mobile")
                        b64 = data.get("data", "")
                        msg_id = data.get("id") or f"audio_{int(time.time() * 1000)}"
                        await ws.send(json.dumps({
                            "action": "upload_audio_ack",
                            "id": msg_id,
                            "ok": bool(b64),
                        }))
                        logger.info("upload_audio_ack sent id=%s ok=%s", msg_id, bool(b64))
                        if self.on_mobile_audio and b64:
                            # Do not run audio/model work on the websocket loop.
                            threading.Thread(target=self.on_mobile_audio, args=(b64,), daemon=True, name="AURA-Mobile-Audio").start()
                        logger.info("mobile audio received (%d chars)", len(b64))

                    elif action == "file_received":
                        self._set_client_source(ws, source or "mobile")
                        filename = data.get("data", "")
                        if self.on_file_received and filename:
                            self.loop.call_soon_threadsafe(self.on_file_received, filename)
                        logger.info("file received: %s", filename)

                except json.JSONDecodeError:
                    logger.warning("invalid websocket json ignored")
                except Exception:
                    logger.exception("websocket message handling failed")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(ws)
            self.client_meta.pop(ws, None)
            logger.info("client disconnected (%d)", len(self.clients))

    async def _run(self):
        self.loop = asyncio.get_running_loop()
        self._stop = asyncio.Event()
        ssl_context = None
        if os.path.exists(_CERT_PATH) and os.path.exists(_KEY_PATH):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(_CERT_PATH, _KEY_PATH)
            logger.info("wss (SSL) enabled")

        self._server = await websockets.serve(
            self._handle,
            WS_HOST,
            WS_PORT,
            ssl=ssl_context,
            ping_interval=30,
            ping_timeout=10,
            max_size=32 * 1024 * 1024,
        )
        proto = "wss" if ssl_context else "ws"
        logger.info("%s server started on %s://%s:%d", proto, proto, WS_HOST, WS_PORT)

        zc = AsyncZeroconf()
        local_ip = _get_local_ip()
        info = AsyncServiceInfo(
            "_aura._tcp.local.",
            "AURA Voice Assistant._aura._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=WS_PORT,
            properties={"path": "/", "version": APP_VERSION},
        )
        await zc.async_register_service(info)
        logger.info("mDNS running at %s:%d", local_ip, WS_PORT)

        await self._stop.wait()
        await zc.async_unregister_service(info)
        await zc.async_close()
        self._server.close()
        await self._server.wait_closed()
        logger.info("server closed")

    def _thread_main(self):
        # Keep the websocket service from silently dying. If the async server
        # raises because of a temporary network/mDNS/websocket error, log it
        # and restart after a short delay instead of closing the whole AURA
        # server process/window.
        while True:
            try:
                asyncio.run(self._run())
                break
            except Exception:
                logger.exception("websocket server crashed; restarting in 2s")
                time.sleep(2)

    def start(self):
        threading.Thread(target=self._thread_main, daemon=True, name="AURA-WS-Server").start()

    def stop(self):
        if self.loop and not self.loop.is_closed() and self._stop is not None:
            self.loop.call_soon_threadsafe(self._stop.set)

    def _send(self, client, payload: str):
        try:
            fut = asyncio.run_coroutine_threadsafe(client.send(payload), self.loop)
            def _done(f):
                try:
                    f.result()
                except Exception:
                    logger.debug("send failed", exc_info=True)
                    self.clients.discard(client)
                    self.client_meta.pop(client, None)
            fut.add_done_callback(_done)
        except Exception:
            logger.debug("send schedule failed", exc_info=True)
            self.clients.discard(client)
            self.client_meta.pop(client, None)

    def broadcast_text(self, text: str, send: bool = False):
        if not self.clients or not self.loop:
            return
        payload = json.dumps({"action": "insert_text", "text": text, "send": True, "source": "server"})
        targets = [c for c in list(self.clients) if self._get_client_source(c) != "mobile"]
        for c in targets:
            self._send(c, payload)
        logger.info("broadcast text to %d clients: %s", len(targets), text)

    def broadcast_image(self, b64: str, msg_id=None, exclude=None):
        if not self.clients or not self.loop:
            return
        payload = json.dumps({"action": "upload_image", "id": msg_id, "data": b64, "source": "server"})
        targets = []
        for c in list(self.clients):
            if c is exclude:
                continue
            # Only browser extension/unknown legacy clients should receive the
            # huge image payload. Never echo it to mobile clients.
            if self._get_client_source(c) == "mobile":
                continue
            targets.append(c)
        for c in targets:
            self._send(c, payload)
        logger.info("broadcast image id=%s to %d non-mobile clients", msg_id, len(targets))

    def send_file_to_mobile(self, filename: str):
        if not self.clients or not self.loop:
            return
        payload = json.dumps({"action": "file_to_mobile", "filename": filename, "source": "server"})
        targets = [c for c in list(self.clients) if self._get_client_source(c) == "mobile"]
        if not targets:
            targets = list(self.clients)
        for c in targets:
            self._send(c, payload)
        logger.info("file_to_mobile sent to %d clients: %s", len(targets), filename)


ws_manager = WebSocketServer()
