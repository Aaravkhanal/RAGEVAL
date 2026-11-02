"""Host token generator writes distinct tokens and can clear a leaked NVIDIA key."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_host_tokens", ROOT / "scripts" / "generate_host_tokens.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)
write_env = mod.write_env


def test_write_env_distinct_tokens_and_clear_nvidia(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "NVIDIA_API_KEY=leaked-placeholder\nRAGEVAL_PUBLIC_TOKEN=same\nRAGEVAL_ADMIN_TOKEN=same\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RAGEVAL_ENV_FILE", str(env_path))
    written = write_env(env_path, rotate_host_tokens=True, clear_nvidia_key=True)
    text = Path(written).read_text(encoding="utf-8")
    assert "leaked-placeholder" not in text
    values = dict(line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#") and "=" in line)
    assert values["NVIDIA_API_KEY"] == ""
    assert values["RAGEVAL_REQUIRE_AUTH"] == "1"
    assert values["RAGEVAL_PUBLIC_TOKEN"]
    assert values["RAGEVAL_ADMIN_TOKEN"]
    assert values["RAGEVAL_PUBLIC_TOKEN"] != values["RAGEVAL_ADMIN_TOKEN"]
    assert len(values["RAGEVAL_PUBLIC_TOKEN"]) >= 32
