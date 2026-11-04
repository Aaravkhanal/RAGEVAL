from scripts.full_database_recovery import source_url, copy_counts, run
import pytest


def test_password_encoding_and_pooler_restriction(monkeypatch):
    monkeypatch.setenv("RAGEVAL_DATABASE_PASSWORD", "test-only@:/value")
    monkeypatch.setenv("RAGEVAL_DATABASE_HOST", "aws-0-test.pooler.supabase.com")
    value = source_url()
    assert "test-only%40%3A%2Fvalue" in value
    assert ":5432/postgres?sslmode=require" in value
    monkeypatch.setenv("RAGEVAL_DATABASE_HOST", "untrusted.example.com")
    with pytest.raises(ValueError):
        source_url()


def test_copy_counts_preserve_empty_and_multiple_tables():
    assert copy_counts(
        'COPY auth.users (id) FROM stdin;\na\nb\n\\.\nCOPY "auth"."identities" (id) FROM stdin;\n\\.\n'
    ) == {"auth.users": 2, "auth.identities": 0}


def test_command_failure_does_not_echo_credentials():
    with pytest.raises(RuntimeError) as exc:
        run(["false", "credential-that-must-not-appear"])
    assert "credential-that-must-not-appear" not in str(exc.value)
