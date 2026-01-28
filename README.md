# myidea

some interesting idea to explore

## WeChat conversation reader (local, consent-driven)

This repo now includes:
- CLI: read a **locally exported** WeChat conversation JSON or Windows WeChat SQLite DB (read-only copy), **only after explicit user consent**. Supports simple local analysis for **emotion summary** and **schedule/plan extraction** (heuristic, no external API).
- GUI: a minimal Tkinter desktop app to pick file/DB, run analysis, and preview results.
- Assistant GUI: a consolidated Tkinter app (`assistant_gui.py`) offering WeChat reading, notes/diary, and todo reminders (local, consent-driven).

### Usage

1. Export the desired conversation from WeChat to a local JSON file.
2. Run:

```bash
# JSON
python wechat_reader.py /path/to/chat.json --consent --preview 3 --emotion --schedule

# Windows DB (read-only copy)
python wechat_reader.py "C:\\path\\to\\Multi.db" --db --talker wxid_xxx --consent --preview 3 --emotion --schedule
# Custom table/fields if schema differs
python wechat_reader.py "C:\\path\\to\\db.db" --db --table MSG --ts-field CreateTime --sender-field StrTalker --text-field StrContent --consent
# With decryption command (example placeholder; requires user-provided tool/keys)
python wechat_reader.py "C:\\path\\to\\encrypted.db" --db --decrypt-cmd "sqlcipher {src} -cmd \"...\" && cp decrypted {dst}" --consent
```

- `--consent` is required to proceed (to ensure explicit permission).
- `--preview` controls how many messages to print (default 5).
- `--emotion` prints a local, keyword/phrase-based sentiment summary（加权计分，含简单否定/强化词、模式匹配；输出包含 score/positive/negative/mood）。
- `--schedule` extracts lines that look like plans/meetings/deadlines with timestamps.
- `--db` treats the path as a WeChat SQLite DB (read-only copy). Use `--talker` to filter by `StrTalker`, and `--limit` to cap rows.
- `--table` / `--ts-field` / `--sender-field` / `--text-field` allow overriding DB schema names.
- `--list-talkers` (GUI button) reads distinct talkers to help selection; for CLI, provide `--talker` directly.
- `--decrypt-cmd` allows calling an external command to produce a decrypted temp DB; placeholders {src} / {dst} are required.

### Notes

- The script performs **no network access**; it only reads the file you point to.
- If `--consent` is omitted, the script will refuse to read the file.
- For DB mode, the file is copied to a temp path and opened read-only; if the DB is encrypted and no key/clear export is provided, reading will fail with an error.
- Analysis is rule-based and local; improve keyword sets as needed for your data.

### GUI (desktop, Tkinter)

Launch:

```bash
python wechat_gui.py
```

Features:
- Select JSON or DB file.
- Toggle DB mode, list/select talker (DB), set preview count (status line shows progress).
- Toggle emotion/schedule analysis; shows weighted emotion summary and plan extraction locally.

### Encryption notice
- If the DB is encrypted (e.g., sqlcipher/custom), you must supply a decrypted export or key via external tooling; this app does not derive keys. Read errors will mention schema/encryption issues.
- To integrate decryption,先用外部工具生成解密后的 SQLite 副本，再将 CLI/GUI 指向该解密文件。

### Assistant GUI (notes, todos, WeChat)
- Launch `python assistant_gui.py`.
- Tabs: WeChat (same consented reading/analysis, plus optional decrypt command), Notes/Diary (add & list), Todos (add with due time; reminders pop up ~5 minutes before due).

### Windows EXE build (optional)
- Requires Python and `pyinstaller` on Windows.
- Run `build_exe.bat` in the repo root; the packaged app will be at `dist/ai_assistant.exe`.
- EXE remains local/offline and still requires user consent for chat access.

---

## 中文说明

### 功能概览
- 微信本地聊天读取（JSON 或 Windows SQLite，需用户同意；可选解密命令）。
- 聊天情绪分析与日程/计划抽取（本地规则、加权情绪计分）。
- 桌面 GUI（WeChat、Notes/Diary、Todos），支持待办提醒（提前约 5 分钟弹窗）。
- 可通过 `assistant_gui.py` 启动，也可使用打包的 Windows EXE（需自备 Python/pyinstaller 构建）。

### 使用示例
```bash
# JSON
python wechat_reader.py /path/to/chat.json --consent --emotion --schedule

# Windows DB + 解密命令（需替换为实际工具/密钥）
python wechat_reader.py "C:\\path\\to\\enc.db" --db --decrypt-cmd "sqlcipher {src} -cmd \"...\" && cp decrypted.db {dst}" --talker wxid_xxx --consent --emotion --schedule
```

### GUI
- `python assistant_gui.py` 启动 AI 助手（含微信、笔记/日记、待办）。
- 待办支持设置截止时间，提前约 5 分钟提醒。

### 打包 EXE（Windows）
- 在仓库根目录执行 `build_exe.bat`，生成 `dist/ai_assistant.exe`。
- 打包后仍为本地离线应用，读取聊天仍需用户明确同意。
