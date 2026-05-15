import base64
import numpy as np


def capture_fullscreen() -> np.ndarray:
    import mss
    with mss.mss() as sct:
        return np.array(sct.grab(sct.monitors[1]))[:, :, :3]


def crop_to_jpeg_base64(img: np.ndarray, x: int, y: int, w: int, h: int) -> str:
    import cv2
    crop = img[y:y + h, x:x + w]
    crop_bgr = crop[:, :, ::-1]
    _, buf = cv2.imencode(".jpg", crop_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"
