from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import DEFAULT_KNOWLEDGE_DIR
from app.use_cases.reindex_knowledge_base import reindex_knowledge_base


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex Markdown knowledge base into pgvector.")
    parser.add_argument(
        "filepath",
        nargs="?",
        default=str(DEFAULT_KNOWLEDGE_DIR),
        help="Path to a knowledge file or directory with Markdown files.",
    )
    args = parser.parse_args()

    indexed_chunks = reindex_knowledge_base(args.filepath)
    print(f"Indexed {indexed_chunks} knowledge chunks from {args.filepath}.")


if __name__ == "__main__":
    main()
