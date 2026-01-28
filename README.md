# myidea

some interesting idea to explore

## WeChat conversation reader (local, consent-driven)

This repo now includes:
- CLI: read a **locally exported** WeChat conversation JSON or Windows WeChat SQLite DB (read-only copy), **only after explicit user consent**. Supports simple local analysis for **emotion summary** and **schedule/plan extraction** (heuristic, no external API).
- GUI: a minimal Tkinter desktop app to pick file/DB, run analysis, and preview results.

### Usage

1. Export the desired conversation from WeChat to a local JSON file.
2. Run:

```bash
# JSON
python wechat_reader.py /path/to/chat.json --consent --preview 3 --emotion --schedule

# Windows DB (read-only copy)
python wechat_reader.py "C:\\path\\to\\Multi.db" --db --talker wxid_xxx --consent --preview 3 --emotion --schedule
```

- `--consent` is required to proceed (to ensure explicit permission).
- `--preview` controls how many messages to print (default 5).
- `--emotion` prints a local, keyword-based sentiment summary of the other participant.
- `--schedule` extracts lines that look like plans/meetings/deadlines with timestamps.
- `--db` treats the path as a WeChat SQLite DB (read-only copy). Use `--talker` to filter by `StrTalker`, and `--limit` to cap rows.

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
- Toggle DB mode, set talker filter, preview count.
- Runs consented read + emotion + schedule analysis locally, showing output in the window.
