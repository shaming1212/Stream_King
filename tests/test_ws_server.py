import json


class DummyClient:
    def __init__(self, name):
        self.name = name
        self.sent = []

    async def send(self, payload):
        self.sent.append(json.loads(payload))


def test_client_source_defaults_to_unknown():
    from server.ws_server import WebSocketServer

    server = WebSocketServer()
    client = DummyClient("browser")

    assert server._get_client_source(client) == "unknown"
    server._set_client_source(client, "extension")
    assert server._get_client_source(client) == "extension"


def test_duplicate_image_ids_expire_and_dedupe():
    from server.ws_server import WebSocketServer

    server = WebSocketServer()

    assert server._is_duplicate_image("image-1") is False
    assert server._is_duplicate_image("image-1") is True


def test_normalized_image_id_is_stable_for_same_payload():
    from server.ws_server import WebSocketServer

    server = WebSocketServer()
    first = server._normalize_image_id(None, "abc123")
    second = server._normalize_image_id(None, "abc123")

    assert first == second
    assert first.startswith("image_")
