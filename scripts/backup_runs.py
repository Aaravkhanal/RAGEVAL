"""Create or restore a consistent archive of the runs volume.

Stop the API and worker before backup or restore so run files cannot change.
"""

from __future__ import annotations

import argparse
import sqlite3
import tarfile
import tempfile
from pathlib import Path


def backup(root: Path, destination: Path) -> None:
    root = root.resolve()
    destination = destination.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    if destination.is_relative_to(root):
        raise ValueError("Backup destination must be outside the runs directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        db_copy = Path(temporary) / "jobs.sqlite3"
        database = root / "jobs.sqlite3"
        if database.exists():
            with sqlite3.connect(database) as source, sqlite3.connect(db_copy) as target:
                source.backup(target)
        with tarfile.open(destination, "w:gz") as archive:
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.relative_to(root)
                if path.name.startswith("jobs.sqlite3"):
                    continue
                archive.add(path, arcname=str(relative), recursive=False)
            if db_copy.exists():
                archive.add(db_copy, arcname="jobs.sqlite3")


def restore(source: Path, root: Path) -> None:
    if root.exists() and any(root.iterdir()):
        raise ValueError("Restore requires an empty destination")
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(source, "r:gz") as archive:
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if not target.is_relative_to(root.resolve()) or not member.isfile():
                raise ValueError(f"Unsafe archive member: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"Unreadable archive member: {member.name}")
            with target.open("wb") as output:
                while block := extracted.read(1024 * 1024):
                    output.write(block)
    database = root / "jobs.sqlite3"
    if database.exists():
        with sqlite3.connect(database) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Restored SQLite database failed integrity check")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("backup", "restore"))
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.action == "backup":
        backup(args.runs_dir, args.archive)
    else:
        restore(args.archive, args.runs_dir)
