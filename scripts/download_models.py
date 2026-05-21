from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download
from dotenv import load_dotenv


REPOS = {
    "deepdoc": "InfiniFlow/deepdoc",
    "concat": "InfiniFlow/text_concat_xgb_v1.0",
}


def format_size(size: int | None) -> str:
    if not size:
        return "-"
    return f"{size / 1024 / 1024:.2f} MB"


def list_files(repo_id: str) -> tuple[list[tuple[str, int | None]], int]:
    info = HfApi().repo_info(repo_id=repo_id, repo_type="model", files_metadata=True)
    rows = []
    total = 0
    for sibling in sorted(info.siblings, key=lambda item: item.rfilename):
        size = getattr(sibling, "size", None)
        rows.append((sibling.rfilename, size))
        total += size or 0
    return rows, total


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Download RAGFlow DeepDoc model files.")
    parser.add_argument(
        "--target",
        default="vendor/ragflow/rag/res/deepdoc",
        help="Local model directory. Default: vendor/ragflow/rag/res/deepdoc",
    )
    parser.add_argument("--mirror", default=os.getenv("HF_ENDPOINT"), help="Optional HuggingFace endpoint mirror.")
    parser.add_argument("--list", action="store_true", help="Only list remote files and sizes.")
    args = parser.parse_args()

    if args.mirror:
        os.environ["HF_ENDPOINT"] = args.mirror

    target = Path(args.target).resolve()
    print(f"Target: {target}")

    grand_total = 0
    for name, repo_id in REPOS.items():
        rows, total = list_files(repo_id)
        grand_total += total
        print(f"\n{name}: {repo_id}")
        for filename, size in rows:
            print(f"  {filename:35s} {format_size(size)}")
        print(f"  TOTAL {format_size(total)}")

        if not args.list:
            snapshot_download(
                repo_id=repo_id,
                repo_type="model",
                local_dir=target,
                local_dir_use_symlinks=False,
            )

    print(f"\nGrand total: {format_size(grand_total)}")
    if not args.list:
        print("Download finished.")


if __name__ == "__main__":
    main()
