"""Pinned corpus checkout. The corpus itself is never vendored."""

from __future__ import annotations

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusSpec:
    """A corpus identified by repository URL and commit, plus its toolchain pin."""

    repo: str
    revision: str
    namespace: str
    lean: str
    mathlib: str


def repo_root() -> Path:
    """Repository root, whether this file is imported from the tree or an install."""
    starts = [Path(__file__).resolve(), Path.cwd().resolve()]
    for start in starts:
        for parent in [start, *start.parents]:
            if (parent / "corpora" / "leanfrontier.toml").is_file():
                return parent
    raise SystemExit("could not find corpora/leanfrontier.toml; run this from the consilean repository")


def load_spec(path: Path) -> CorpusSpec:
    """Load a corpus pin from a TOML file."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return CorpusSpec(
        repo=data["repo"],
        revision=data["revision"],
        namespace=data["namespace"],
        lean=data["lean"],
        mathlib=data["mathlib"],
    )


def ensure_checkout(spec: CorpusSpec, cache: Path, *, override_env: str | None = "CONSILEAN_LEANFRONTIER") -> Path:
    """Return a checkout of `spec.revision`.

    `CONSILEAN_LEANFRONTIER`, when set, must already be that commit.
    Pass `override_env=None` for a different corpus. Otherwise the commit
    is fetched into `cache`.
    """
    override = os.environ.get(override_env) if override_env else None
    if override:
        return _require_pin(Path(override).resolve(), spec.revision)
    if _head(cache) == spec.revision:
        return cache
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not (cache / ".git").is_dir():
        if cache.exists() and any(cache.iterdir()):
            raise SystemExit(f"{cache} exists but is not a git checkout of the pinned corpus")
        _git(["init", str(cache)])
    if not _remote_configured(cache):
        _git(["-C", str(cache), "remote", "add", "origin", spec.repo])
    _git(["-C", str(cache), "fetch", "--depth", "1", "origin", spec.revision])
    _git(["-C", str(cache), "checkout", "--detach", "FETCH_HEAD"])
    return _require_pin(cache, spec.revision)


def _require_pin(root: Path, revision: str) -> Path:
    head = _head(root)
    if head != revision:
        raise SystemExit(f"{root} is at {head}, pinned revision is {revision}")
    return root


def _head(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _remote_configured(root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "remote"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "origin" in result.stdout.split()


def _git(args: list[str]) -> None:
    result = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
