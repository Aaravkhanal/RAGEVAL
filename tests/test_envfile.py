"""Gitignored .env loader does not overwrite live environment values."""

from rageval.core.envfile import load_dotenv_file, parse_env_text


def test_parse_env_text_ignores_comments():
    values = parse_env_text("# hi\nNVIDIA_API_KEY=abc\nOPENAI_API_KEY=\"quoted\"\n")
    assert values["NVIDIA_API_KEY"] == "abc"
    assert values["OPENAI_API_KEY"] == "quoted"


def test_load_dotenv_file_does_not_overwrite(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("NVIDIA_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setenv("NVIDIA_API_KEY", "from-env")
    load_dotenv_file(path, overwrite=False)
    assert path.read_text(encoding="utf-8").count("from-file") == 1
    from os import environ

    assert environ["NVIDIA_API_KEY"] == "from-env"
