from __future__ import annotations

import argparse
import json
import logging
import sys

from dotenv import load_dotenv

from .config import load_config
from .publish import publish_daily, today_iso


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(
        description="Publish daily Fitbit health data to Intervals.icu",
    )
    parser.add_argument(
        "--date",
        dest="date",
        default=today_iso(),
        help="Date to publish (YYYY-MM-DD). Defaults to today.",
    )
    args = parser.parse_args()

    config = load_config()
    result = publish_daily(config, args.date)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
