import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_CACHE_DIR = os.path.join(ROOT_DIR, "models")
MODEL_NAME = "iic/SenseVoiceSmall"
VAD_MODEL = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
PUNC_MODEL = "iic/punc_ct-transformer_cn-en-common-vocab471067-large"

SAMPLE_RATE = 16000

HOTKEY_VOICE = "alt+1"
HOTKEY_CAMERA = "alt+2"
HOTKEY_SCREENSHOT = "alt+3"

WS_HOST = "127.0.0.1"
WS_PORT = 8765

os.environ["MODELSCOPE_CACHE"] = MODEL_CACHE_DIR
