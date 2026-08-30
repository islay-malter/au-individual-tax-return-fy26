from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "validate_evals.py"
MANIFEST_PATH = SKILL_DIR / "evals" / "cases.json"


class EvalManifestCliTests(unittest.TestCase):
    def test_committed_manifest_validates_without_claiming_behavior_ran(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(MANIFEST_PATH), "--json"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["manifest_valid"])
        self.assertFalse(report["behavior_run"])


if __name__ == "__main__":
    unittest.main()
