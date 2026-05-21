from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_host: str = "0.0.0.0"
    app_port: int = 8010
    app_workers: int = 1

    storage_dir: Path = Path("app/storage")
    max_upload_mb: int = 128
    default_language: str = "Chinese"
    default_parser_mode: str = "auto"
    max_page_number: int = 1000

    layout_recognizer_type: str = "onnx"
    parallel_devices: int = 0
    pdf_parser_page_batch_size: int = 50
    hf_endpoint: str | None = "https://hf-mirror.com"

    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])

    @property
    def upload_dir(self) -> Path:
        return self.project_root / self.storage_dir / "uploads"

    @property
    def result_dir(self) -> Path:
        return self.project_root / self.storage_dir / "results"

    @property
    def vendor_ragflow_dir(self) -> Path:
        return self.project_root / "vendor" / "ragflow"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)
    return settings
