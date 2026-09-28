#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search the MapleStory GMS database JSON for entries.

Usage:
  python search_db.py "<keyword>"                 # fuzzy search on name/tags/content
  python search_db.py "" --type item             # list all entries of a type
  python search_db.py "紫苹果" --name            # exact name match
  python search_db.py --db <path>                # custom db path (default assets/maplestory_db.json)
"""
import argparse
import json
import os
import sys

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "assets", "maplestory_db.json")


def load_db(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def norm(s):
    return (s or "").strip().lower()


def match(entry, keyword, exact_name=False):
    if exact_name:
        names = [norm(entry.get("name_zh", "")), norm(entry.get("name_en", ""))]
        return any(n == norm(keyword) for n in names if n)
    kw = norm(keyword)
    if not kw:
        return True  # no keyword -> match all (used with --type filter)
    haystack = " ".join([
        norm(entry.get("name_zh", "")),
        norm(entry.get("name_en", "")),
        norm(entry.get("content", "")),
        " ".join(norm(t) for t in entry.get("tags", [])),
    ])
    return kw in haystack


def main():
    ap = argparse.ArgumentParser(description="Search MapleStory GMS database")
    ap.add_argument("keyword", nargs="?", default="")
    ap.add_argument("--type", default=None, help="filter by entry type")
    ap.add_argument("--name", action="store_true", help="exact name match")
    ap.add_argument("--db", default=DEFAULT_DB, help="path to db json")
    args = ap.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"ERROR: database not found: {db_path}")
        sys.exit(1)

    db = load_db(db_path)
    results = []
    for e in db.get("entries", []):
        if args.type and norm(e.get("type")) != norm(args.type):
            continue
        if match(e, args.keyword, exact_name=args.name):
            results.append(e)

    if not results:
        print("NO_RESULT")
        sys.exit(0)

    for i, e in enumerate(results, 1):
        print(f"[{i}] id={e.get('id')} type={e.get('type')}")
        print(f"    name_zh={e.get('name_zh')}  name_en={e.get('name_en')}")
        content = e.get("content", "")
        print(f"    content={content}")
        print(f"    tags={e.get('tags')}  source={e.get('source')}  added_at={e.get('added_at')}")
        print()


if __name__ == "__main__":
    main()
