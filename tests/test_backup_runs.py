import sqlite3

from scripts.backup_runs import backup, restore


def test_runs_backup_restore_round_trip(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    with sqlite3.connect(runs / "jobs.sqlite3") as db:
        db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY, state TEXT)")
        db.execute("INSERT INTO jobs VALUES ('one', 'complete')")
    result = runs / "one"
    result.mkdir()
    (result / "metrics.json").write_text('{"n": 1}')
    archive = tmp_path / "runs.tar.gz"
    backup(runs, archive)
    restored = tmp_path / "restored"
    restore(archive, restored)
    assert (restored / "one" / "metrics.json").read_text() == '{"n": 1}'
    with sqlite3.connect(restored / "jobs.sqlite3") as db:
        assert db.execute("SELECT state FROM jobs WHERE id='one'").fetchone()[0] == "complete"
