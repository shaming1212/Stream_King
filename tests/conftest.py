import sys
import types


def _install_stub(name, module):
    if name not in sys.modules:
        sys.modules[name] = module


numpy = types.ModuleType("numpy")


class _NdArray:
    pass


numpy.ndarray = _NdArray
numpy.float32 = float
numpy.int16 = int
numpy.concatenate = lambda chunks, axis=0: chunks[0] if chunks else []
numpy.squeeze = lambda value: value
numpy.frombuffer = lambda *_args, **_kwargs: []
numpy.array = lambda value: value
_install_stub("numpy", numpy)


keyboard = types.ModuleType("keyboard")
keyboard.unhook_all = lambda: None
keyboard.add_hotkey = lambda *args, **kwargs: None
keyboard.on_release_key = lambda *args, **kwargs: None
keyboard.is_pressed = lambda *_args, **_kwargs: False
_install_stub("keyboard", keyboard)


sounddevice = types.ModuleType("sounddevice")


class _InputStream:
    def __init__(self, *args, **kwargs):
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def close(self):
        self.started = False


sounddevice.InputStream = _InputStream
_install_stub("sounddevice", sounddevice)


cv2 = types.ModuleType("cv2")
cv2.IMWRITE_JPEG_QUALITY = 1


class _VideoCapture:
    def __init__(self, *_args, **_kwargs):
        self.released = False

    def isOpened(self):
        return False

    def read(self):
        return False, None

    def release(self):
        self.released = True


cv2.VideoCapture = _VideoCapture
cv2.imencode = lambda *_args, **_kwargs: (True, b"")
_install_stub("cv2", cv2)


qtcore = types.ModuleType("PyQt6.QtCore")


class _Signal:
    def __init__(self, *_args, **_kwargs):
        self.calls = []

    def emit(self, *args):
        self.calls.append(args)


class _QObject:
    def __init__(self, *_args, **_kwargs):
        pass


class _QThread:
    def __init__(self, *_args, **_kwargs):
        pass

    def start(self):
        self.run()

    def run(self):
        pass


class _QCoreApplication:
    _instance = None

    def __init__(self, *_args, **_kwargs):
        _QCoreApplication._instance = self

    @classmethod
    def instance(cls):
        return cls._instance


qtcore.QObject = _QObject
qtcore.QThread = _QThread
qtcore.QCoreApplication = _QCoreApplication
qtcore.pyqtSignal = lambda *args, **kwargs: _Signal()

pyqt6 = types.ModuleType("PyQt6")
pyqt6.QtCore = qtcore
_install_stub("PyQt6", pyqt6)
_install_stub("PyQt6.QtCore", qtcore)


websockets = types.ModuleType("websockets")
websockets.serve = lambda *args, **kwargs: None


class _ConnectionClosed(Exception):
    pass


websockets.exceptions = types.SimpleNamespace(ConnectionClosed=_ConnectionClosed)
_install_stub("websockets", websockets)


zeroconf = types.ModuleType("zeroconf")
zeroconf_asyncio = types.ModuleType("zeroconf.asyncio")


class _AsyncServiceInfo:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class _AsyncZeroconf:
    async def async_register_service(self, *_args, **_kwargs):
        return None

    async def async_unregister_service(self, *_args, **_kwargs):
        return None

    async def async_close(self):
        return None


zeroconf_asyncio.AsyncServiceInfo = _AsyncServiceInfo
zeroconf_asyncio.AsyncZeroconf = _AsyncZeroconf
_install_stub("zeroconf", zeroconf)
_install_stub("zeroconf.asyncio", zeroconf_asyncio)
