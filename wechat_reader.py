"""Simple, consent-driven WeChat chat reader.

This module provides a minimal example of how one might load a locally
exported WeChat conversation file *after* obtaining explicit user
permission. It intentionally avoids any network access and only reads
files that the user points to.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


Message = Dict[str, Any]


def _load_chat_file(chat_path: Path) -> List[Message]:
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


def read_conversation_json(chat_path: str, consent: bool) -> List[Message]:
    """Read a locally exported WeChat JSON conversation after consent is granted.

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


def _copy_readonly_db(db_path: Path) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    shutil.copyfile(db_path, tmp.name)
    return Path(tmp.name)


def read_conversation_sqlite(
    db_path: str,
    consent: bool,
    talker: Optional[str] = None,
    limit: Optional[int] = None,
    table: str = "MSG",
    ts_field: str = "CreateTime",
    sender_field: str = "StrTalker",
    text_field: str = "StrContent",
) -> List[Message]:
    """Read a conversation from a WeChat SQLite DB (Windows) in read-only mode.

    Expects a table `MSG` with columns CreateTime (int seconds), StrTalker, StrContent.
    If schema differs or DB is encrypted, raises ValueError.
    """
    if not consent:
        raise PermissionError("User consent is required before reading chats.")

    path = Path(db_path).expanduser().resolve()
    copied = _copy_readonly_db(path)
    try:
        conn = sqlite3.connect(f"file:{copied}?mode=ro", uri=True)
        cur = conn.cursor()
        where_clause = ""
        params: List[Any] = []
        if talker:
            where_clause = f"WHERE {sender_field} = ?"
            params.append(talker)
        order_clause = f"ORDER BY {ts_field}"
        limit_clause = ""
        if limit:
            limit_clause = "LIMIT ?"
            params.append(limit)
        sql = f"SELECT {ts_field}, {sender_field}, {text_field} FROM {table} {where_clause} {order_clause} {limit_clause};"
        try:
            rows = cur.execute(sql, params).fetchall()
        except sqlite3.DatabaseError as exc:
            raise ValueError("Failed to read DB (schema mismatch or encrypted).") from exc
    finally:
        try:
            copied.unlink()
        except OSError:
            pass

    messages: List[Message] = []
    for ts_raw, talker_raw, content in rows:
        messages.append(
            {
                "timestamp": _normalize_timestamp(ts_raw),
                "sender": talker_raw,
                "text": content,
            }
        )
    return messages


def _normalize_timestamp(ts: Any) -> Any:
    if isinstance(ts, (int, float)):
        try:
            # Heuristic: if seconds value seems in ms, divide
            if ts > 32503680000:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts)
        except Exception:
            return ts
    return ts


def _extract_timestamp(msg: Message) -> Optional[datetime]:
    ts = msg.get("timestamp") or msg.get("time") or msg.get("ts")
    if ts is None:
        return None
    # Accept int (ms or s) or ISO string
    try:
        if isinstance(ts, (int, float)):
            # Heuristic: if larger than year 3000 in seconds, treat as ms
            if ts > 32503680000:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts)
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts)
            except ValueError:
                # common format: "YYYY-MM-DD HH:MM:SS"
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
                    try:
                        return datetime.strptime(ts, fmt)
                    except ValueError:
                        continue
    except Exception:
        return None
    return None


def summarize_emotion(messages: Iterable[Message]) -> Dict[str, Any]:
    """Rule-based emotion tagging with weighted keywords."""
    positive_keywords = {
        "好": 2,
        "谢谢": 1,
        "开心": 3,
        "赞": 2,
        "可以": 1,
        "行": 1,
        "yes": 1,
        "ok": 1,
        "great": 3,
        "love": 3,
    }
    negative_keywords = {
        "不好": 2,
        "生气": 3,
        "烦": 2,
        "不行": 2,
        "no": 1,
        "不": 1,
        "差": 1,
        "伤心": 3,
        "哭": 2,
        "讨厌": 3,
    }

    counts = Counter()
    score = 0
    for msg in messages:
        text = str(msg.get("text") or msg.get("content") or "").lower()
        sender = msg.get("sender") or msg.get("from")
        role = msg.get("role")
        if role not in (None, "other") and sender in (None, "other"):
            # assume 'role' overrides sender
            pass
        is_other = role == "other" or sender not in (None, "me", "self")
        if not is_other:
            continue
        for k, w in positive_keywords.items():
            if k in text:
                counts["positive"] += 1
                score += w
        for k, w in negative_keywords.items():
            if k in text:
                counts["negative"] += 1
                score -= w
    total = counts["positive"] + counts["negative"]
    mood = "neutral"
    if total:
        if score > 0:
            mood = "positive"
        elif score < 0:
            mood = "negative"
    return {
        "mood": mood,
        "positive": counts["positive"],
        "negative": counts["negative"],
        "score": score,
    }


def list_talkers_sqlite(
    db_path: str,
    consent: bool,
    table: str = "MSG",
    sender_field: str = "StrTalker",
) -> List[str]:
    """List distinct talkers from a WeChat SQLite DB (read-only copy)."""
    if not consent:
        raise PermissionError("User consent is required before reading chats.")
    path = Path(db_path).expanduser().resolve()
    copied = _copy_readonly_db(path)
    try:
        conn = sqlite3.connect(f"file:{copied}?mode=ro", uri=True)
        cur = conn.cursor()
        sql = f"SELECT DISTINCT {sender_field} FROM {table} LIMIT 200;"
        try:
            rows = cur.execute(sql).fetchall()
        except sqlite3.DatabaseError as exc:
            raise ValueError("Failed to read DB (schema mismatch or encrypted).") from exc
    finally:
        try:
            copied.unlink()
        except OSError:
            pass
    return [r[0] for r in rows if r and r[0]]


def extract_schedules(messages: Iterable[Message]) -> List[Dict[str, Any]]:
    """Extract simple schedule/plan items using keyword heuristics."""
    schedule_keywords = {"明天", "后天", "周", "星期", "下周", "安排", "会议", "开会", "deadline", "ddl", "计划", "目标"}
    date_prefixes = ("20", "19")  # rough ISO-like dates

    results: List[Dict[str, Any]] = []
    for msg in messages:
        text = str(msg.get("text") or msg.get("content") or "")
        if any(k in text for k in schedule_keywords) or text.strip().startswith(date_prefixes):
            results.append(
                {
                    "text": text,
                    "timestamp": _extract_timestamp(msg),
                    "sender": msg.get("sender") or msg.get("from"),
                }
            )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read a local WeChat conversation after user consent."
    )
    parser.add_argument(
        "chat_path",
        help="Path to exported conversation JSON file or WeChat SQLite DB.",
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
    parser.add_argument(
        "--db",
        action="store_true",
        help="Treat chat_path as a WeChat SQLite DB (Windows) instead of JSON.",
    )
    parser.add_argument(
        "--talker",
        help="For DB mode: talker/wxid to filter messages (StrTalker).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="For DB mode: limit number of messages read.",
    )
    parser.add_argument("--table", default="MSG", help="DB table name (default: MSG).")
    parser.add_argument("--ts-field", default="CreateTime", help="DB timestamp field.")
    parser.add_argument("--sender-field", default="StrTalker", help="DB sender field.")
    parser.add_argument("--text-field", default="StrContent", help="DB content field.")
    parser.add_argument(
        "--emotion",
        action="store_true",
        help="Run simple local emotion summary on other participant messages.",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Extract simple schedule/plan mentions (heuristic).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.consent:
        parser.error("Refusing to read chat without --consent.")

    if args.db:
        messages = read_conversation_sqlite(
            args.chat_path,
            consent=True,
            talker=args.talker,
            limit=args.limit,
            table=args.table,
            ts_field=args.ts_field,
            sender_field=args.sender_field,
            text_field=args.text_field,
        )
    else:
        messages = read_conversation_json(args.chat_path, consent=True)
    preview_count = max(args.preview, 0)
    for msg in messages[:preview_count]:
        print(json.dumps(msg, ensure_ascii=False))

    if args.emotion:
        summary = summarize_emotion(messages)
        print("# Emotion summary")
        print(json.dumps(summary, ensure_ascii=False, default=str))

    if args.schedule:
        schedules = extract_schedules(messages)
        print("# Schedule/plan items")
        for item in schedules:
            item_out = dict(item)
            if isinstance(item_out.get("timestamp"), datetime):
                item_out["timestamp"] = item_out["timestamp"].isoformat()
            print(json.dumps(item_out, ensure_ascii=False))


if __name__ == "__main__":
    main()
