import argparse
import sys

sys.path.insert(0, "src")

from polymarket.refresh_catalog import refresh_catalog


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--incremental",
        "-i",
        action="store_true",
        help="newest-first pages only until a full page is already in the db (skips closed detection)",
    )
    args = p.parse_args()
    refresh_catalog(incremental=args.incremental, quiet=False)
