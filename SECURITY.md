# Security Policy

## Supported Versions

AURA is currently in an early open-source stage. Security fixes are expected to target the latest code on the `main` branch unless a tagged release states otherwise.

## Reporting a Vulnerability

Please do not open a public GitHub issue for sensitive security reports.

If you discover a vulnerability, report it privately through GitHub Security Advisories when available, or contact the maintainer through the GitHub profile linked from this repository.

Please include:

- A short description of the issue
- Steps to reproduce the behavior
- Affected components, such as desktop app, WebSocket server, browser extension, Android client, or packaged release
- Any relevant logs, screenshots, proof of concept, or environment details
- Whether the issue may expose local files, local network access, credentials, microphone data, screenshots, or browser content

## Response Expectations

The maintainer will make a best effort to:

- Acknowledge valid reports as soon as possible
- Reproduce and assess the impact
- Prepare a fix or mitigation before public disclosure when appropriate
- Credit reporters when requested and safe to do so

## Security Scope

AURA connects local desktop, voice, browser, and mobile workflows. Reports are especially helpful for issues involving:

- Unauthorized local WebSocket access
- Unsafe file server exposure
- Browser extension message handling
- Local data leakage from screenshots, history, logs, or clipboard content
- Packaged dependency vulnerabilities
- Android-to-desktop pairing or network discovery risks

## User Safety Notes

Users should only run AURA on trusted machines and networks. Avoid exposing local service ports directly to the public internet.
