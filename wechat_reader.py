"""Simple, consent-driven WeChat chat reader.

This module provides a minimal example of how one might load a locally
exported WeChat conversation file *after* obtaining explicit user
permission. It intentionally avoids any network access and only reads
files that the user points to.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_chat_file(chat_path: Path) -> List[Dict[str, Any]]:
    """Load chat messages from a JSON file.

    The file is expected to contain a list of message objects. Invalid files
    result in a ValueError with a concise message.
    """
    try:
        content = chat_path.read_text(encoding="utf-8")
        return json.loads(content)
    except FileNotFoundError as exc:
        raise ValueError(f"Chat file not found: {chat_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Chat file is not valid JSON: {chat_path}") from exc


def read_conversation(chat_path: str, consent: bool) -> List[Dict[str, Any]]:
    """Read a locally exported WeChat conversation after consent is granted.

    Args:
        chat_path: Path to the exported conversation JSON file.
        consent: Whether the user has explicitly granted permission.

    Returns:
        Parsed list of messages.

    Raises:
        PermissionError: If consent was not granted.
        ValueError: For missing or malformed files.
    """
    if not consent:
        raise PermissionError("User consent is required before reading chats.")

    path = Path(chat_path).expanduser().resolve()
    return _load_chat_file(path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read a local WeChat conversation after user consent."
    )
    parser.add_argument(
        "chat_path",
        help="Path to exported conversation JSON file (local only).",
    )
    parser.add_argument(
        "--consent",
        action="store_true",
        help="Confirm that you have explicit permission to read this chat.",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=5,
        help="Number of messages to preview (default: 5).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.consent:
        parser.error("Refusing to read chat without --consent.")

    messages = read_conversation(args.chat_path, consent=True)
    preview_count = max(args.preview, 0)
    for msg in messages[:preview_count]:
        print(json.dumps(msg, ensure_ascii=False))


if __name__ == "__main__":
    main()
