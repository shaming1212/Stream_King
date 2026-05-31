# Contributing To AURA

> Status: Draft. This contribution guide is proposed and not final.

Thank you for considering a contribution. AURA is currently a local-first voice, browser, mobile, and multimodal bridge. Contributions can be small and still valuable: a bug report, a website adapter fix, a better README section, or a test for one difficult edge case.

## Ways To Help

- [ ] Report startup, microphone, browser extension, or mobile pairing issues.
- [ ] Add or repair an AI site adapter in `extension/content.js`.
- [ ] Improve local network discovery and connection diagnostics.
- [ ] Add tests for `core/`, `server/`, and extension behavior.
- [ ] Improve documentation for Windows, Android, Chrome, and model setup.
- [ ] Help design the future plugin and device mesh architecture.

## Local Development

```bash
pip install -r requirements.txt
python main.py
```

Planned development improvements:

- [ ] Add a dedicated developer setup guide.
- [ ] Add a reproducible packaged build guide.
- [ ] Add a minimal fake ASR mode for UI and server testing.
- [ ] Add browser-extension test fixtures.

## Adding A Browser Adapter

Most AI page support lives in `extension/content.js`.

Proposed adapter checklist:

- [ ] Identify stable input selectors.
- [ ] Identify send button selectors.
- [ ] Choose image injection mode: file input, drag/drop, or clipboard hint.
- [ ] Test text insertion.
- [ ] Test image insertion.
- [ ] Test duplicate-image prevention.
- [ ] Document any site-specific limitations.

## Pull Request Expectations

- [ ] Explain the problem and the user-facing impact.
- [ ] Keep changes scoped.
- [ ] Add or update tests when practical.
- [ ] Update docs when behavior changes.
- [ ] Avoid committing secrets, private keys, local credentials, or personal logs.
- [ ] Use Git LFS for large binary assets when required.

## Project Values

- [ ] Local-first when possible.
- [ ] Privacy-aware by default.
- [ ] Clear user feedback over silent failure.
- [ ] Open adapters and inspectable behavior.
- [ ] Practical reliability before speculative complexity.

