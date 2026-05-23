AURA Server V5 changes

1. ASR default changed from large model to small profile:
   - default AURA_MODEL_PROFILE=small
   - default MODEL_NAME=iic/SenseVoiceSmall
   - punc model disabled by default to reduce download size, memory and startup time

2. You can switch back to the old large model without editing code:
   Windows PowerShell:
     $env:AURA_MODEL_PROFILE="large"; python main.py
   Linux/macOS:
     AURA_MODEL_PROFILE=large python main.py

3. Image forwarding duplicate fix:
   - server upload_image path now has one authoritative broadcast path only
   - on_mobile_image callback is no longer called for mobile image forwarding
   - this avoids GUI callback + ws broadcast injecting the same phone screenshot/photo twice

4. Kept previous V4 ACK behavior:
   - server ACKs upload_image immediately
   - image is forwarded to non-mobile clients only
