"""Regenerate the Sprint 1 ranking from the pinned LeanFrontier corpus."""

from __future__ import annotations

import argparse

from consilean.ingest.corpus import ensure_checkout, load_spec, repo_root
from consilean.sprint1.report import build_report, print_report, write_generated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = repo_root()
    spec = load_spec(root / "corpora" / "leanfrontier.toml")
    checkout = ensure_checkout(spec, root / "corpora" / "cache" / "LeanFrontier")
    report = build_report(checkout, spec)
    json_path, md_path = write_generated(root, report)
    print_report(report)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
