from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.localisation import request_language, localise_error_detail


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.auto_create_schema:
        import app.models  # noqa: F401
        from app.db.base import Base
        from app.db.session import engine

        Base.metadata.create_all(bind=engine)
        from app.db.schema import ensure_profile_extensions

        ensure_profile_extensions(engine)
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/api/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @application.middleware("http")
    async def add_security_headers(request: Request, call_next):
        language = 'zh' if request.headers.get('Accept-Language', '').lower().startswith('zh') else 'en'
        token = request_language.set(language)
        try:
            response = await call_next(request)
        finally:
            request_language.reset(token)
        response.headers['Content-Language'] = 'zh-CN' if language == 'zh' else 'en-GB'
        vary = response.headers.get('Vary', '')
        response.headers['Vary'] = ', '.join(dict.fromkeys([*(part.strip() for part in vary.split(',') if part.strip()), 'Accept-Language']))
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith(settings.api_prefix):
            response.headers.setdefault("Cache-Control", "no-store")
        if settings.app_env.casefold() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @application.exception_handler(StarletteHTTPException)
    async def translated_http_error(request: Request, exc: StarletteHTTPException):
        translated = StarletteHTTPException(exc.status_code, localise_error_detail(exc.detail), headers=exc.headers)
        return await http_exception_handler(request, translated)

    @application.exception_handler(RequestValidationError)
    async def translated_validation_error(request: Request, exc: RequestValidationError):
        errors = localise_error_detail(exc.errors())
        return await request_validation_exception_handler(request, RequestValidationError(errors, body=exc.body))

    application.include_router(api_router, prefix=settings.api_prefix)

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir() and (frontend_dist / "index.html").is_file():
        application.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @application.get("/{requested_path:path}", include_in_schema=False)
        def serve_frontend(requested_path: str) -> FileResponse:
            candidate = (frontend_dist / requested_path).resolve()
            if frontend_dist.resolve() in candidate.parents and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(frontend_dist / "index.html", headers={"Cache-Control": "no-cache"})
    return application


app = create_app()
