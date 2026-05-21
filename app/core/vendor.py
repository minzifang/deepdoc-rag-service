import os
import sys
import types
from pathlib import Path

from app.core.config import get_settings


def bootstrap_ragflow_vendor() -> Path:
    """Expose vendored RAGFlow modules without booting the whole RAGFlow platform."""

    settings = get_settings()
    vendor_dir = settings.vendor_ragflow_dir
    if not vendor_dir.exists():
        raise RuntimeError(f"RAGFlow vendor directory not found: {vendor_dir}")

    os.environ.setdefault("RAG_PROJECT_BASE", str(vendor_dir))
    os.environ.setdefault("LAYOUT_RECOGNIZER_TYPE", settings.layout_recognizer_type)
    os.environ.setdefault("PDF_PARSER_PAGE_BATCH_SIZE", str(settings.pdf_parser_page_batch_size))
    if settings.hf_endpoint:
        os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)

    vendor_path = str(vendor_dir)
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)

    # The official DeepDoc parser only needs a tiny slice of common.settings for
    # standalone parsing. Importing the real settings module pulls in database,
    # storage, api and memory services, so we provide a narrow compatibility shim.
    settings_module = sys.modules.get("common.settings")
    if settings_module is None:
        settings_module = types.ModuleType("common.settings")
        sys.modules["common.settings"] = settings_module

    settings_module.PARALLEL_DEVICES = settings.parallel_devices
    settings_module.LAYOUT_RECOGNIZER_TYPE = settings.layout_recognizer_type
    settings_module.DOC_ENGINE_INFINITY = False
    settings_module.DOC_MAXIMUM_SIZE = settings.max_upload_mb * 1024 * 1024
    settings_module.DOC_BULK_SIZE = 4
    settings_module.EMBEDDING_BATCH_SIZE = 16

    return vendor_dir
