#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search all JSON databases under assets/ for entries.

By default it scans every *.json file under the assets/ directory and searches
across all of them (maplestory_db.json, auto_db.json, ...). Each hit is tagged
with the file it came from.

Context filtering: entries tagged as season/context-locked (e.g. tag "CW限定")
are hidden when the query is unrelated to that context. Asking about CW/H凯
keeps them visible; use --all to force showing everything.

Usage:
  python search_db.py "<keyword>"                 # fuzzy search all assets/*.json
  python search_db.py "" --type item              # list all entries of a type (across all db)
  python search_db.py "紫苹果" --name              # exact name match (across all)
  python search_db.py "凶星" --db assets/auto_db.json   # search a single custom db file
  python search_db.py "辉耀" --all                 # include context-locked entries
"""
import argparse
import glob
import json
import os
import sys

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "assets")

# Query substrings that indicate the user is asking in the CW-season context.
CW_CONTEXT_KEYWORDS = ["cw", "挑战", "冠军", "赛季", "champion",
                       "h凯", "困凯", "困难凯"]


def load_db(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def norm(s):
    return (s or "").strip().lower()


def is_cw_context(keyword):
    k = norm(keyword)
    return any(w in k for w in CW_CONTEXT_KEYWORDS)


def is_cw_locked(entry):
    """An entry carrying the tag 'CW限定' only exists in the CW season."""
    return any(norm(t) == "cw限定" for t in entry.get("tags", []))


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


def collect_db_paths(db_arg):
    """Return the list of json files to search.

    - if db_arg is a directory: all *.json files directly under it
    - if db_arg is a file: just that file
    - otherwise: error
    """
    p = os.path.abspath(db_arg)
    if os.path.isdir(p):
        return sorted(glob.glob(os.path.join(p, "*.json")))
    if os.path.isfile(p):
        return [p]
    return []


def main():
    ap = argparse.ArgumentParser(description="Search MapleStory GMS databases (all assets/*.json)")
    ap.add_argument("keyword", nargs="?", default="")
    ap.add_argument("--type", default=None, help="filter by entry type")
    ap.add_argument("--name", action="store_true", help="exact name match")
    ap.add_argument("--all", action="store_true",
                    help="show every entry, including context-locked (e.g. CW-season-only) entries")
    ap.add_argument("--db", default=ASSETS_DIR,
                    help="db file or assets dir to search (default: all assets/*.json)")
    args = ap.parse_args()

    db_paths = collect_db_paths(args.db)
    if not db_paths:
        print(f"ERROR: no json database found under: {os.path.abspath(args.db)}")
        sys.exit(1)

    # Hide context-locked entries unless the query is in that context or --all is given.
    hide_locked = not args.all and not is_cw_context(args.keyword)

    results = []
    for db_path in db_paths:
        try:
            db = load_db(db_path)
        except Exception as exc:
            print(f"WARNING: skipped unreadable db {db_path}: {exc}")
            continue
        db_file = os.path.basename(db_path)
        for e in db.get("entries", []):
            if args.type and norm(e.get("type")) != norm(args.type):
                continue
            if hide_locked and is_cw_locked(e):
                continue
            if match(e, args.keyword, exact_name=args.name):
                results.append((db_file, e))

    if not results:
        print("NO_RESULT")
        sys.exit(0)

    print(f"SEARCHED {len(db_paths)} db file(s): {', '.join(os.path.basename(p) for p in db_paths)}")
    if hide_locked:
        print("CONTEXT: context-locked entries hidden (use --all to show them)")
    for i, (db_file, e) in enumerate(results, 1):
        print(f"[{i}] id={e.get('id')} type={e.get('type')}  db={db_file}")
        print(f"    name_zh={e.get('name_zh')}  name_en={e.get('name_en')}")
        content = e.get("content", "")
        print(f"    content={content}")
        print(f"    tags={e.get('tags')}  source={e.get('source')}  added_at={e.get('added_at')}")
        print()


if __name__ == "__main__":
    main()
