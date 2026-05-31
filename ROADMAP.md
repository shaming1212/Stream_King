# AURA Roadmap Draft

> Status: Draft. All items are proposed work until explicitly marked complete in a future release.

This roadmap is intentionally ambitious. It describes the path from the current local voice assistant toward a local-first multimodal AI interaction platform.

## Phase 1: Local Voice Assistant

- [ ] Stabilize push-to-talk voice capture across Windows machines.
- [ ] Improve ASR startup state, loading feedback, and error messages.
- [ ] Add clearer model profile selection for small, large, and future local models.
- [ ] Document microphone permissions and common Windows audio issues.
- [ ] Add regression tests around hotkey flow and ASR pipeline state.

## Phase 2: Browser AI Bridge

- [ ] Maintain adapters for ChatGPT, DeepSeek, Kimi, Doubao, Tongyi, Gemini, Claude, Perplexity, Poe, Copilot, and Grok.
- [ ] Add an adapter test harness using local DOM fixtures.
- [ ] Add health checks for extension-to-desktop WebSocket connectivity.
- [ ] Create a guide for contributors to add new AI site adapters.
- [ ] Build safer fallback behavior when a target site changes its DOM.

## Phase 3: Mobile Companion

- [ ] Document Android installation and pairing in English and Chinese.
- [ ] Add a clear device discovery screen and connection diagnostics.
- [ ] Support mobile audio upload, image upload, and file handoff as stable flows.
- [ ] Define a versioned mobile-to-desktop message protocol.
- [ ] Add QR-code pairing as an alternative to mDNS discovery.

## Phase 4: Local Device Mesh

- [ ] Move from one desktop endpoint to a trusted local device network.
- [ ] Add device identity, trust prompts, and revocation.
- [ ] Support multiple phones, tablets, laptops, and browser clients.
- [ ] Add per-device permissions for text, image, audio, and file events.
- [ ] Build a local dashboard for connected devices and active streams.

## Phase 5: Realtime Multimodal Stream Layer

- [ ] Explore WebRTC for low-latency audio, video, and screen streams.
- [ ] Add realtime captions from microphone and mobile sources.
- [ ] Add OCR over screenshots and video frames.
- [ ] Add optional local vision model processing.
- [ ] Support recording, replay, and timeline-based review of multimodal sessions.

## Phase 6: Plugin And Adapter Ecosystem

- [ ] Define a plugin manifest for adapters, tools, and workflows.
- [ ] Create examples for browser adapters, model adapters, and automation hooks.
- [ ] Add a plugin registry format that can work without a central server.
- [ ] Support community-maintained integrations.
- [ ] Add security guidance for plugin review and permissions.

## Phase 7: Local AI Operating Layer

- [ ] Provide a local command bus for human intent, device events, and AI agents.
- [ ] Add workflow automation across browser tabs, files, mobile input, and local models.
- [ ] Integrate with developer tools, OBS, Home Assistant, creative tools, and IDEs.
- [ ] Make AURA scriptable through CLI and SDK entry points.
- [ ] Turn AURA into a reusable local runtime for personal AI systems.

## Release Quality Goals

- [ ] Document every supported platform and limitation.
- [ ] Add smoke tests for desktop startup, WebSocket server, extension routing, and file transfer.
- [ ] Add reproducible build instructions for the packaged Windows release.
- [ ] Keep large release assets in Git LFS or GitHub Releases.
- [ ] Publish checksums for packaged binaries.

