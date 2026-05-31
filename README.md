# AURA Voice Assistant

AURA is a local AI voice assistant and browser injection bridge. It turns speech, screenshots, camera captures, and mobile uploads into text or image payloads that can be inserted into supported AI chat pages through a local WebSocket service and a Chrome extension.

Repository: [shaming1212/Stream_King](https://github.com/shaming1212/Stream_King)

## Open Source Notice

AURA is an open-source project released under the MIT License. You are welcome to study, use, improve, and contribute to the project under the terms of the repository license.

Before using, redistributing, packaging, or contributing code, please follow:

- The [MIT License](LICENSE) for this repository's source code.
- The licenses of third-party dependencies, including PyQt6, FunASR, ModelScope, OpenCV, Torch, and browser-extension platform APIs.
- The licenses and usage terms of bundled or downloaded speech models.
- The rules of the AI websites that AURA integrates with through browser adapters.

See [Third-Party Notices](THIRD_PARTY_NOTICES.md) for dependency, model, browser, and packaged-release considerations. Packaged binaries and model files may include additional third-party terms beyond the repository source-code license.

## What It Does

- Runs a PyQt6 desktop assistant on Windows.
- Records voice with a push-to-talk hotkey and transcribes it locally with FunASR.
- Uses SenseVoiceSmall by default, with an FSMN VAD model for speech activity detection.
- Sends recognized text to browser AI chat pages through a Manifest V3 extension.
- Captures camera frames and screen selections, copies them to the clipboard, and forwards them to connected clients.
- Accepts Android mobile audio/image uploads over the local network.
- Publishes a local WebSocket server on port `8765`, a temporary file-transfer server on port `8766`, and mDNS discovery on UDP `5353`.

## Supported AI Sites

The browser extension includes adapters or fallbacks for:

- ChatGPT
- DeepSeek
- Kimi
- Doubao
- Tongyi
- Gemini
- Claude
- Perplexity
- Poe
- Microsoft Copilot
- Grok

## Source Project Structure

```text
core/                       Core engines independent from the GUI
  config.py                 Hotkeys, model profile, cache path, and ports
  voice_engine.py           FunASR speech recognition pipeline
  camera_engine.py          OpenCV camera capture
  clipboard_util.py         Clipboard image helpers
  history_store.py          Local history persistence
  screenshot_tool.py        Screen capture helper

gui/                        PyQt6 desktop interface
  main_window.py            Floating main window and hotkey wiring
  signal_bridge.py          Thread-safe signal bridge
  style.qss                 Dark UI styling
  widgets/                  Reusable UI widgets

server/                     Local communication layer
  ws_server.py              WebSocket server and client broadcast logic
  file_server.py            Temporary file download server

extension/                  Chrome/Edge Manifest V3 extension
  manifest.json             Permissions and supported AI site matches
  background.js             Local WebSocket client and tab routing
  content.js                Site adapters for text and image injection
  popup/                    Extension popup

tampermonkey/               Optional userscript fallback
tests/                      Unit tests
docs/                       Architecture and user documentation
main.py                     Desktop application entry point
requirements.txt            Python runtime dependencies
```

## Newly Added Release Structure

Compared with the source repository, this update adds the complete local packaged release under `release/AURA_Package_20260524/`.

```text
release/AURA_Package_20260524/
  AURA.exe                  Packaged Windows desktop/server application
  Start_AURA_Server.bat     Preflight check and one-click launcher
  _internal/                Bundled Python runtime, PyQt6, Torch, OpenCV, FunASR, and native DLLs
  extension/                Browser extension copy used by the packaged build
  mobile/                   Android APK package
  models/                   Local ModelScope cache with SenseVoiceSmall and FSMN VAD models
  history/                  Captured voice/image history from the packaged app
  logs/                     Runtime logs from the packaged app
  README.md                 Release-specific usage notes
```

Large files in the release directory are tracked with Git LFS, including `.exe`, `.dll`, `.pyd`, `.pt`, `.apk`, images, audio, and archive files.

## Quick Start From Source

```bash
pip install -r requirements.txt
python main.py
```

On first launch, AURA downloads speech models into `models/` unless the cache already exists. The default profile uses `iic/SenseVoiceSmall` and `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`.

## Quick Start From Packaged Release

1. Open `release/AURA_Package_20260524/`.
2. Run `Start_AURA_Server.bat`.
3. If Windows firewall prompts appear, allow local network access.
4. Load `release/AURA_Package_20260524/extension/` from `chrome://extensions/` in developer mode.
5. Install `release/AURA_Package_20260524/mobile/app-arm64-v8a-release.apk` on an Android phone if mobile upload is needed.
6. Keep the phone and PC on the same LAN for mDNS discovery.

## Hotkeys

| Hotkey | Action |
| --- | --- |
| `Alt + 1` | Hold to record voice, release to transcribe and inject text |
| `Alt + 2` | Capture camera image and inject/upload it |
| `Alt + 3` | Select a screen region and inject/upload it |

## Ports

| Port | Protocol | Purpose |
| --- | --- | --- |
| `8765` | TCP | WebSocket text/image/audio bridge |
| `8766` | TCP | Temporary file transfer to mobile clients |
| `5353` | UDP | mDNS local discovery |

## Development Notes

- Change hotkeys and ports in `core/config.py`.
- Keep `extension/background.js` `WS_URL` aligned with the desktop WebSocket port.
- Do not publish extension private keys such as `.pem` files.
- Git LFS is required before cloning or pushing the complete release package.

```bash
git lfs install
git lfs pull
```
