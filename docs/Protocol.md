# AURA Local Protocol

This document describes the current local WebSocket message contract between the desktop server, browser extension, and Android companion. It is intentionally small and reflects the existing implementation.

## Transport

- WebSocket server: `ws://<desktop-host>:8765`
- File transfer server: `http://<desktop-host>:8766/api/download/<filename>`
- Discovery: mDNS service `_aura._tcp.local.`

## Client Identification

Clients may include a `source` field in any message.

Known sources:

- `extension`
- `mobile`
- `server`

Unknown clients are treated as browser-compatible legacy clients unless marked as `mobile`.

## Messages

### `client_hello`

Sent by clients after connecting.

```json
{ "action": "client_hello", "source": "extension" }
```

Server response:

```json
{ "action": "client_hello_ack", "ok": true }
```

### `ping`

Heartbeat message.

```json
{ "action": "ping", "source": "extension", "ts": 1710000000000 }
```

Server response:

```json
{ "action": "pong" }
```

### `upload_audio`

Sent by mobile clients with base64 WAV data.

```json
{ "action": "upload_audio", "source": "mobile", "id": "audio_1", "data": "..." }
```

Server response:

```json
{ "action": "upload_audio_ack", "id": "audio_1", "ok": true }
```

### `upload_image`

Sent by mobile clients or the desktop server with a base64 image payload.

```json
{ "action": "upload_image", "source": "mobile", "id": "image_1", "data": "..." }
```

Server response to mobile upload:

```json
{ "action": "upload_image_ack", "id": "image_1", "ok": true }
```

The server forwards image payloads only to non-mobile clients to avoid echoing large images back to the phone.

### `insert_text`

Sent by the desktop server to browser-compatible clients.

```json
{ "action": "insert_text", "source": "server", "text": "hello", "send": true }
```

### `file_to_mobile`

Sent by the desktop server when a file is ready for mobile download.

```json
{ "action": "file_to_mobile", "source": "server", "filename": "example.zip" }
```

### `file_received`

Sent by the mobile client after a file download is complete.

```json
{ "action": "file_received", "source": "mobile", "data": "example.zip" }
```
