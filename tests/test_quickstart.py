import os
import stat
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
QUICKSTART_SCRIPT = ROOT_DIR / "scripts" / "quickstart.sh"
README = ROOT_DIR / "README.md"


def test_quickstart_script_dry_run_documents_bootstrap_steps(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text("#!/usr/bin/env bash\necho fake uv \"$@\"\n", encoding="utf-8")
    fake_uv.chmod(fake_uv.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [str(QUICKSTART_SCRIPT), "--dry-run"],
        check=False,
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert ".env.example" in result.stdout
    assert "Would run: uv sync" in result.stdout
    assert "Would run: uv run llm-training-tools" in result.stdout
    assert "http://127.0.0.1:5000" in result.stdout


def test_readme_quickstart_uses_frictionless_script():
    readme = README.read_text(encoding="utf-8")

    assert "./scripts/quickstart.sh" in readme
    assert "uv run llm-training-tools" in readme
    assert "LLMTOOLS_DB_PATH=src/data/qa_data.db" in readme
