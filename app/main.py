from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.vendor import bootstrap_ragflow_vendor


def create_app() -> FastAPI:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)
    bootstrap_ragflow_vendor()

    app = FastAPI(
        title="DeepDoc Parse Service",
        version="0.1.0",
        description="Standalone RAGFlow DeepDoc parsing service.",
    )
    app.include_router(router)
    web_dir = Path(__file__).resolve().parent / "web"
    app.mount("/assets", StaticFiles(directory=web_dir), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/ui", include_in_schema=False)
    def test_page() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()
