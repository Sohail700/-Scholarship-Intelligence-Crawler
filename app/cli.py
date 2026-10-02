from __future__ import annotations

import argparse
import json

from .crawler import Crawler
from .database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlas Scholarship Intelligence Crawler")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    sub.add_parser("seed-demo")
    sub.add_parser("crawl")
    sub.add_parser("stats")
    args = parser.parse_args()
    db = Database()

    if args.cmd == "init-db":
        db.init()
        print(f"Database initialized at {db.path}")
    elif args.cmd == "seed-demo":
        from scripts.seed_demo import seed
        seed()
    elif args.cmd == "crawl":
        result = Crawler().run()
        print(json.dumps(result, indent=2))
    elif args.cmd == "stats":
        print(json.dumps(db.stats(), indent=2))


if __name__ == "__main__":
    main()
