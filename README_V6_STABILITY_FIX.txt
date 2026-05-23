AURA V6 stability fix

1. WebSocket server thread now logs crashes and restarts instead of silently exiting.
2. _stop event is created inside the running event loop to avoid loop-binding issues.
3. upload_audio now sends upload_audio_ack immediately and processes audio in a worker thread, not on the websocket loop.
4. Fixed mobile WAV resampling logic to avoid oversized/invalid audio arrays.
5. Image ACK/forwarding logic from V5 is preserved.

Test: start server, connect mobile, confirm server window does not close, then test voice upload.
