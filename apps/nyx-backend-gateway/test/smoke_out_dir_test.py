import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_smoke_out_dir_creates_marker():
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "nyx_smoke_all_modules.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable,
            str(script),
            "--dry-run",
            "--out-dir",
            tmpdir,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        marker = Path(tmpdir) / "dry_run.txt"
        assert marker.exists()
