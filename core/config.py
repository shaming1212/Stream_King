import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_CACHE_DIR = os.path.join(ROOT_DIR, "models")

# ASR model profile:
#   small = lower memory / faster startup / better for old machines
#   large = previous Paraformer large + punc model
# You can override every model by environment variables without editing code:
#   AURA_MODEL_PROFILE=large
#   AURA_MODEL_NAME=...
#   AURA_VAD_MODEL=...
#   AURA_PUNC_MODEL=...
MODEL_PROFILE = os.getenv("AURA_MODEL_PROFILE", "small").strip().lower()

_SMALL_MODEL_NAME = "iic/SenseVoiceSmall"
_LARGE_MODEL_NAME = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
_DEFAULT_VAD_MODEL = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
_LARGE_PUNC_MODEL = "iic/punc_ct-transformer_cn-en-common-vocab471067-large"

if MODEL_PROFILE == "large":
    MODEL_NAME = os.getenv("AURA_MODEL_NAME", _LARGE_MODEL_NAME)
    VAD_MODEL = os.getenv("AURA_VAD_MODEL", _DEFAULT_VAD_MODEL)
    PUNC_MODEL = os.getenv("AURA_PUNC_MODEL", _LARGE_PUNC_MODEL)
else:
    MODEL_NAME = os.getenv("AURA_MODEL_NAME", _SMALL_MODEL_NAME)
    VAD_MODEL = os.getenv("AURA_VAD_MODEL", _DEFAULT_VAD_MODEL)
    # SenseVoiceSmall normally does not need the large punctuation model.
    # Leave empty by default to reduce download size, memory and startup cost.
    PUNC_MODEL = os.getenv("AURA_PUNC_MODEL", "")

SAMPLE_RATE = 16000

HOTKEY_VOICE = "alt+1"
HOTKEY_CAMERA = "alt+2"
HOTKEY_SCREENSHOT = "alt+3"

APP_VERSION = os.getenv("AURA_VERSION", "1.0")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


WS_HOST = os.getenv("AURA_WS_HOST", "0.0.0.0")
WS_PORT = _env_int("AURA_WS_PORT", 8765)
FILE_HOST = os.getenv("AURA_FILE_HOST", "0.0.0.0")
FILE_PORT = _env_int("AURA_FILE_PORT", 8766)

os.environ["MODELSCOPE_CACHE"] = MODEL_CACHE_DIR
