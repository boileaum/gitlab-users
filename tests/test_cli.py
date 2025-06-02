import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_CLI = REPO_ROOT / "src" / "gitlab_users" / "gitlab_users.py"


def test_cli_help():
    result = subprocess.run(
        [sys.executable, str(SRC_CLI), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
