# Third-Party Notices

AURA uses open-source libraries, platform APIs, and downloadable model assets. Contributors and downstream users must follow the license terms of this repository and the terms of every dependency, model, platform, and service they use with it.

## Runtime Dependencies

Key dependency families include:

- PyQt6
- websockets
- keyboard
- sounddevice
- numpy
- scipy
- FunASR
- ModelScope
- OpenCV
- mss
- zeroconf
- ifaddr

This list is informational and may not be exhaustive. Check `requirements.txt`, packaged release contents, and dependency metadata for the authoritative license terms.

## Models

The packaged release and default runtime may use ModelScope-hosted speech models, including SenseVoiceSmall and FSMN VAD model assets. Model files can have terms that are separate from this repository's source-code license.

Before redistributing model weights or packaged releases that include model files, verify the corresponding model license and usage restrictions.

## Browser And AI Site Integrations

AURA includes browser adapters for AI websites. Users and contributors are responsible for following the terms, automation policies, and acceptable-use rules of each website they connect to.

## Packaged Releases

Packaged binaries may contain third-party runtime files and native libraries. Redistributors should preserve license notices and verify whether a binary redistribution has obligations beyond the repository source license.
