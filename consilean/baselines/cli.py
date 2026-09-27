"""Regenerate the Sprint 0 LeanFrontier baselines from the pinned corpus."""

from __future__ import annotations

import argparse

from consilean.baselines.report import build_report, print_report, write_generated
from consilean.ingest.corpus import ensure_checkout, load_spec, repo_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="fetch the pinned LeanFrontier commit and exit",
    )
    args = parser.parse_args()
    root = repo_root()
    spec = load_spec(root / "corpora" / "leanfrontier.toml")
    checkout = ensure_checkout(spec, root / "corpora" / "cache" / "LeanFrontier")
    if args.fetch_only:
        print(checkout)
        return
    report = build_report(checkout, spec)
    json_path, md_path = write_generated(root, report)
    print_report(report)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
