# myidea

some interesting idea to explore

## WeChat conversation reader (local, consent-driven)

This repo now includes a minimal example script that reads a **locally exported** WeChat conversation JSON file, **only after explicit user consent**. It adds simple local analysis for **emotion summary** and **schedule/plan extraction** (purely heuristic, no external API).

### Usage

1. Export the desired conversation from WeChat to a local JSON file.
2. Run:

```bash
python wechat_reader.py /path/to/chat.json --consent --preview 3 --emotion --schedule
```

- `--consent` is required to proceed (to ensure explicit permission).
- `--preview` controls how many messages to print (default 5).
- `--emotion` prints a local, keyword-based sentiment summary of the other participant.
- `--schedule` extracts lines that look like plans/meetings/deadlines with timestamps.

### Notes

- The script performs **no network access**; it only reads the file you point to.
- If `--consent` is omitted, the script will refuse to read the file.
- Analysis is rule-based and local; improve keyword sets as needed for your data.
