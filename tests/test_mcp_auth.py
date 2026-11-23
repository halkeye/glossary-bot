import asyncio

from gloss.mcp_auth import BearerAuthMiddleware

TOKEN = "test-token"


async def ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def call(app, path="/mcp", authorization=None, scope_type="http"):
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("utf-8")))
    scope = {
        "type": scope_type,
        "method": "POST",
        "path": path,
        "headers": headers,
    }
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def status(sent):
    return sent[0]["status"]


def headers(sent):
    return dict(sent[0]["headers"])


class TestBearerAuthMiddleware:
    def setup_method(self):
        self.app = BearerAuthMiddleware(ok_app, token=TOKEN, exempt_paths={"/healthz"})

    def test_missing_header_is_rejected(self):
        sent = call(self.app)

        assert status(sent) == 401
        assert headers(sent)[b"www-authenticate"] == b"Bearer"

    def test_wrong_scheme_is_rejected(self):
        sent = call(self.app, authorization=f"Token {TOKEN}")

        assert status(sent) == 401

    def test_wrong_token_is_rejected(self):
        sent = call(self.app, authorization="Bearer wrong")

        assert status(sent) == 401

    def test_correct_token_is_allowed(self):
        sent = call(self.app, authorization=f"Bearer {TOKEN}")

        assert status(sent) == 200

    def test_bearer_scheme_is_case_insensitive(self):
        sent = call(self.app, authorization=f"bearer {TOKEN}")

        assert status(sent) == 200

    def test_exempt_path_does_not_require_a_token(self):
        sent = call(self.app, path="/healthz")

        assert status(sent) == 200

    def test_non_http_scope_passes_through(self):
        seen = []

        async def record_app(scope, receive, send):
            seen.append(scope["type"])

        app = BearerAuthMiddleware(record_app, token=TOKEN)
        call(app, scope_type="lifespan")

        assert seen == ["lifespan"]

    def test_empty_token_is_rejected_at_construction(self):
        try:
            BearerAuthMiddleware(ok_app, token="")
        except ValueError as exc:
            assert "MCP_AUTH_TOKEN" in str(exc)
        else:
            raise AssertionError("expected ValueError")
