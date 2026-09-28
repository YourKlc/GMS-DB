#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add an entry to the MapleStory GMS database with structural validation.

Usage:
  python add_entry.py --type item --name_zh "紫苹果" --name_en "Purple Apple" \
      --content "消耗品。使用时恢复 500 点 HP。" --tags 消耗品 恢复 \
      --source user

Notes:
  - id is auto-generated from type + running number if not provided.
  - --name_zh is required; duplicate name_zh causes a merge prompt (won't auto-add).
  - --db defaults to assets/maplestory_db.json.
"""
import argparse
import json
import os
import sys
import datetime

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "assets", "maplestory_db.json")

VALID_TYPES = {"item", "job", "quest", "map", "boss", "npc", "system", "guide", "event"}
REQUIRED = {"type", "name_zh", "content", "source"}


def load_db(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_db(db, path):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def next_id(db, etype):
    entries = db.get("entries", [])
    n = 0
    prefix = f"{etype}_"
    for e in entries:
        i = e.get("id", "")
        if i.startswith(prefix):
            try:
                n = max(n, int(i.split("_")[1]))
            except (IndexError, ValueError):
                pass
    return f"{prefix}{n + 1:04d}"


def main():
    ap = argparse.ArgumentParser(description="Add entry to MapleStory GMS database")
    ap.add_argument("--type", required=True, help="entry type: " + ", ".join(sorted(VALID_TYPES)))
    ap.add_argument("--name_zh", required=True, help="Chinese name / aliases")
    ap.add_argument("--name_en", default="")
    ap.add_argument("--content", default="")
    ap.add_argument("--tags", nargs="*", default=[])
    ap.add_argument("--image_url", default="")
    ap.add_argument("--source", default="user", help="user or wiki")
    ap.add_argument("--added_at", default="")
    ap.add_argument("--db", default=DEFAULT_DB, help="path to db json")
    args = ap.parse_args()

    etype = args.type.strip().lower()
    if etype not in VALID_TYPES:
        print(f"ERROR: invalid type '{etype}'. Valid: {', '.join(sorted(VALID_TYPES))}")
        sys.exit(1)
    if not args.name_zh.strip():
        print("ERROR: --name_zh is required")
        sys.exit(1)
    if not args.content.strip():
        print("WARNING: content is empty; will record entry with empty details")

    db_path = os.path.abspath(args.db)
    db = load_db(db_path)

    # duplicate check on name_zh (merge, don't auto-add)
    for e in db.get("entries", []):
        if e.get("name_zh") == args.name_zh.strip():
            print(f"DUPLICATE: name_zh '{args.name_zh}' already exists as id={e.get('id')}.")
            print("Merge into existing entry instead of adding a duplicate.")
            sys.exit(2)

    added_at = args.added_at or datetime.date.today().isoformat()
    entry = {
        "id": next_id(db, etype),
        "type": etype,
        "name_zh": args.name_zh.strip(),
        "name_en": args.name_en.strip(),
        "content": args.content.strip(),
        "tags": list(args.tags),
        "image_url": args.image_url.strip(),
        "source": args.source.strip() or "user",
        "added_at": added_at,
    }
    db.setdefault("entries", []).append(entry)
    db["version"] = db.get("version", 1) + 1
    db["updated_at"] = datetime.date.today().isoformat()

    save_db(db, db_path)
    print(f"ADDED id={entry['id']} type={entry['type']} name_zh={entry['name_zh']}")
    print(f"Total entries now: {len(db['entries'])}")


if __name__ == "__main__":
    main()
