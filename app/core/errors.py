from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _error_payload(code: str, message: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(exc.code, exc.message))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("internal_error", str(exc)),
        )
