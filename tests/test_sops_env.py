"""Regression tests for the encrypted environment launcher."""

from pathlib import Path


def test_sops_env_never_sources_decrypted_values():
    script = Path("scripts/sops-env").read_text(encoding="utf-8")

    assert 'source "$TMPFILE"' not in script
    assert "bash -c" not in script
    assert "--output-type json" in script
    assert "os.execvpe" in script
