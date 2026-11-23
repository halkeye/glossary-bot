"""ASGI bearer-token authentication for the MCP endpoint."""

import hmac

from starlette.responses import PlainTextResponse


class BearerAuthMiddleware:
    """Require ``Authorization: Bearer <token>`` on HTTP requests.

    ``exempt_paths`` are passed through unauthenticated (used for health checks).
    Non-HTTP ASGI scopes (for example lifespan) are never blocked.
    """

    def __init__(self, app, token: str, exempt_paths=()):
        if not token:
            raise ValueError("MCP_AUTH_TOKEN must not be empty")
        self.app = app
        self._token = token.encode("utf-8")
        self.exempt_paths = frozenset(exempt_paths)

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("path") in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        scheme, _, credentials = headers.get(b"authorization", b"").partition(b" ")
        if scheme.lower() != b"bearer" or not hmac.compare_digest(
            credentials, self._token
        ):
            response = PlainTextResponse(
                "Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
