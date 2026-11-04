"""Supabase-aware logical database backup with an isolated local restore check.

Requires a source database password. The REST/service key is insufficient.
Never restores to the hosted source; restore DB is loopback-only and disposable.
"""

import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote
from scripts.protected_backup import encrypt_snapshot

PROJECT = "hqrwjhwpnceyygumnpjv"
EXPECTED = (
    "public.rageval_records",
    "public.rageval_jobs",
    "auth.users",
    "auth.identities",
)


def source_url():
    password = os.environ.get("RAGEVAL_DATABASE_PASSWORD", "")
    host = os.environ.get("RAGEVAL_DATABASE_HOST", "")
    if (
        not password
        or not host.endswith(".pooler.supabase.com")
        or not re.fullmatch(r"[a-zA-Z0-9.-]+", host)
    ):
        raise ValueError(
            "Configure the source database password and Supabase session-pooler host"
        )
    return (
        "postgresql://postgres."
        + PROJECT
        + ":"
        + quote(password, safe="")
        + "@"
        + host
        + ":5432/postgres?sslmode=require"
    )


def run(args, **kwargs):
    # Suppress subprocess argument dumps: dump arguments contain the source URI.
    completed = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if completed.returncode:
        raise RuntimeError(
            "Database recovery command failed at "
            + args[0]
            + "; credential values and SQL output were withheld"
        )
    return completed.stdout.strip()


def copy_counts(sql):
    counts = {}
    current = None
    for line in sql.splitlines():
        if line.startswith("COPY ") and line.rstrip().endswith("FROM stdin;"):
            current = line[5:].split(" (", 1)[0].replace('"', "")
            counts[current] = 0
        elif current and line == "\\.":
            current = None
        elif current:
            counts[current] += 1
    return counts


def backup_and_verify(output):
    source = source_url()
    source_major = (
        int(
            run(
                [
                    "psql",
                    "--dbname=" + source,
                    "-At",
                    "--command",
                    "show server_version_num;",
                ]
            )
        )
        // 10000
    )
    if source_major != 17:
        raise ValueError(
            "Source database major version changed; update the compatible restore image before proceeding"
        )
    with tempfile.TemporaryDirectory(prefix="rageval-full-") as folder:
        folder = Path(folder)
        files = {}
        for name, flags in [
            ("roles.sql", ["--role-only"]),
            ("schema.sql", []),
            (
                "data.sql",
                [
                    "--data-only",
                    "--use-copy",
                    "-x",
                    "storage.buckets_vectors",
                    "-x",
                    "storage.vector_indexes",
                ],
            ),
        ]:
            path = folder / name
            run(
                [
                    "supabase",
                    "db",
                    "dump",
                    "--remote=" + source,
                    "-f",
                    str(path),
                    *flags,
                ]
            )
            files[name] = path
        counts = copy_counts(files["data.sql"].read_text())
        if any(table not in counts for table in EXPECTED):
            raise ValueError(
                "Dump did not explicitly include all application/Auth tables"
            )
        work = folder / "restore"
        run(["supabase", "init", "--workdir", str(work)])
        config = work / "supabase" / "config.toml"
        config.write_text(
            re.sub(
                r"(?m)^major_version\s*=\s*\d+",
                "major_version = 17",
                config.read_text(),
            )
        )
        try:
            run(["supabase", "db", "start", "--workdir", str(work)])
            target = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
            run(
                [
                    "psql",
                    "--single-transaction",
                    "--variable",
                    "ON_ERROR_STOP=1",
                    "--file",
                    str(files["roles.sql"]),
                    "--file",
                    str(files["schema.sql"]),
                    "--command",
                    "SET session_replication_role = replica",
                    "--file",
                    str(files["data.sql"]),
                    "--dbname",
                    target,
                ]
            )
            verified = {}
            for table in EXPECTED:
                count = int(
                    run(
                        [
                            "psql",
                            "--dbname",
                            target,
                            "-At",
                            "--variable",
                            "ON_ERROR_STOP=1",
                            "--command",
                            "select count(*) from " + table,
                        ]
                    )
                )
                if count != counts[table]:
                    raise ValueError("Restored row count differs for " + table)
                verified[table] = count
            package = {
                "schema": "rageval.supabase_full_backup.v1",
                "project": PROJECT,
                "files": {
                    name: base64.b64encode(path.read_bytes()).decode()
                    for name, path in files.items()
                },
                "verified_rows": verified,
                "scope": "Supabase logical roles/schema/data including Auth users and identities; Storage binaries and platform settings excluded",
            }
            digest = encrypt_snapshot(package, output)
            return {
                "status": "passed",
                "verified_rows": verified,
                "encrypted_sha256": digest,
                "scope": package["scope"],
            }
        finally:
            subprocess.run(
                ["supabase", "stop", "--workdir", str(work), "--no-backup"],
                capture_output=True,
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="rageval-full-database.enc")
    args = parser.parse_args()
    print(json.dumps(backup_and_verify(args.output)))
