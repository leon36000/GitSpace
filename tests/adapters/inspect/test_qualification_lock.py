from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

from common import INSPECT_COMMIT, INSPECT_VERSION, INSPECT_WHEEL_SHA256

SDIST_SHA256 = "785a14b5348c57a188e8790a1919106bff539645d93c4e9d1dfdd8f2b0896405"


class InspectQualificationLockTests(unittest.TestCase):
    def test_qualification_manifest_and_uv_lock_bind_the_same_release(self) -> None:
        root = Path(__file__).resolve().parents[3]
        qualification = json.loads(
            (
                root
                / "docs"
                / "phase-00"
                / "qualifications"
                / "inspect-ai-0.3.258.json"
            ).read_text(encoding="utf-8")
        )
        lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
        packages = [
            package
            for package in lock["package"]
            if package["name"] == "inspect-ai"
        ]

        self.assertEqual(len(packages), 1)
        package = packages[0]
        self.assertEqual(package["version"], INSPECT_VERSION)
        self.assertEqual(
            package["sdist"]["hash"],
            f"sha256:{SDIST_SHA256}",
        )
        wheels = {
            Path(wheel["url"]).name: wheel["hash"]
            for wheel in package["wheels"]
        }
        self.assertEqual(
            wheels["inspect_ai-0.3.258-py3-none-any.whl"],
            f"sha256:{INSPECT_WHEEL_SHA256}",
        )

        self.assertEqual(qualification["version"], INSPECT_VERSION)
        self.assertEqual(qualification["tag"], INSPECT_VERSION)
        self.assertEqual(qualification["source_commit"], INSPECT_COMMIT)
        self.assertEqual(
            qualification["package"]["wheel"]["sha256"],
            INSPECT_WHEEL_SHA256,
        )
        self.assertEqual(
            qualification["package"]["sdist"]["sha256"],
            SDIST_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
