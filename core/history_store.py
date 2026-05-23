import os
import json
import base64
import datetime

from core.config import ROOT_DIR

HISTORY_DIR = os.path.join(ROOT_DIR, "history")
IMAGES_DIR = os.path.join(HISTORY_DIR, "images")
INDEX_PATH = os.path.join(HISTORY_DIR, "history.json")

os.makedirs(IMAGES_DIR, exist_ok=True)


class HistoryStore:
    def __init__(self):
        self.records: list = []
        self._load()

    def add_voice(self, text: str):
        record = {"type": "voice", "text": text,
                  "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.records.append(record)
        self._save()
        return record

    def add_image(self, b64: str, img_type: str = "screenshot"):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{img_type}_{ts}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        parts = b64.split(",")
        data = parts[1] if len(parts) > 1 else b64
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        record = {"type": img_type, "file": filepath, "filename": filename,
                  "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.records.append(record)
        self._save()
        return record

    def _save(self):
        data = []
        for r in self.records:
            d = {"type": r["type"], "time": r["time"]}
            if r["type"] == "voice":
                d["text"] = r["text"]
            else:
                d["filename"] = r.get("filename", "")
                d["file"] = r.get("file", "")
            data.append(d)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        if not os.path.exists(INDEX_PATH):
            self.records = []
            return
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.records = data
        except Exception:
            self.records = []

    def clear(self):
        self.records = []
        self._save()
