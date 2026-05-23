import ctypes
import struct
import logging

logger = logging.getLogger("clipboard")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Ensure correct return types on 64-bit Windows (handles are pointer-sized)
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

CF_DIB = 8
GHND = 0x0042


def _img_to_dib_bgr(img) -> bytes:
    """Convert numpy BGR image to Windows DIB (BITMAPINFOHEADER + pixel data)."""
    import numpy as np
    h, w = img.shape[:2]
    if img.ndim == 3 and img.shape[2] == 3:
        bgra = np.zeros((h, w, 4), dtype=np.uint8)
        bgra[:, :, :3] = img[:, :, ::-1]  # BGR -> BGRA
        bgra[:, :, 3] = 255
    else:
        bgra = np.repeat(img[:, :, np.newaxis], 4, axis=2) if img.ndim == 2 else img
        bgra[:, :, [0, 1, 2]] = bgra[:, :, [2, 1, 0]]

    # BMP rows must be 4-byte aligned (already aligned since w*4)
    pixel_data = bgra.tobytes()
    # Use negative height for top-down pixel order (matches numpy array layout)
    header = struct.pack('<IiiHHIIiiII',
                         40, w, -h, 1, 32, 0, len(pixel_data), 2835, 2835, 0, 0)
    return header + pixel_data


def set_clipboard_image(img) -> bool:
    """Set a numpy BGR image (from OpenCV) onto the Windows system clipboard."""
    try:
        dib = _img_to_dib_bgr(img)
    except Exception as e:
        logger.error("image to DIB failed: %s", e)
        return False

    if not user32.OpenClipboard(None):
        logger.warning("OpenClipboard failed")
        return False
    try:
        user32.EmptyClipboard()
        h = kernel32.GlobalAlloc(GHND, len(dib))
        if not h:
            logger.warning("GlobalAlloc failed")
            return False
        p = kernel32.GlobalLock(h)
        if not p:
            logger.warning("GlobalLock failed")
            return False
        ctypes.memmove(p, dib, len(dib))
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_DIB, h)
        logger.info("image set on clipboard (%dx%d, %d bytes)", img.shape[1], img.shape[0], len(dib))
        return True
    except Exception as e:
        logger.error("set clipboard failed: %s", e)
        return False
    finally:
        user32.CloseClipboard()
