from __future__ import annotations

import json
import pathlib
import tomllib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class ToolchainContractTests(unittest.TestCase):
    def test_exact_toolchain_contract(self) -> None:
        required = [
            ROOT / "toolchains.lock.json",
            ROOT / "rust-toolchain.toml",
            ROOT / "Cargo.toml",
            ROOT / "pyproject.toml",
            ROOT / ".gitignore",
        ]
        for path in required:
            self.assertTrue(path.is_file(), f"missing required file: {path.name}")

        lock = json.loads((ROOT / "toolchains.lock.json").read_text(encoding="utf-8"))
        rust = tomllib.loads((ROOT / "rust-toolchain.toml").read_text(encoding="utf-8"))
        cargo = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertEqual(lock["schema_version"], 1)
        self.assertEqual(lock["rust"]["version"], "1.97.1")
        self.assertEqual(lock["python"]["version"], "3.12.13")
        self.assertEqual(lock["uv"]["version"], "0.12.0")
        self.assertEqual(lock["checked_at"], "2026-08-13")
        self.assertEqual(lock["compatibility"]["harbor_requires_python"], ">=3.12")
        self.assertEqual(lock["compatibility"]["inspect_evals_min_python"], ">=3.11")
        self.assertEqual(lock["compatibility"]["inspect_evals_preferred_series"], ["3.11", "3.12"])

        self.assertEqual(rust["toolchain"]["channel"], "1.97.1")
        self.assertEqual(rust["toolchain"]["profile"], "minimal")
        self.assertEqual(set(rust["toolchain"]["components"]), {"clippy", "rustfmt"})
        self.assertEqual(cargo["workspace"]["members"], [])
        self.assertEqual(cargo["workspace"]["resolver"], "3")
        self.assertEqual(pyproject["project"]["requires-python"], "==3.12.13")
        self.assertFalse(pyproject["tool"]["uv"]["package"])
        self.assertEqual(pyproject["tool"]["gitspace"]["uv-version"], "0.12.0")

        for item in ("target/", "__pycache__/", ".venv/", ".pytest_cache/", ".ruff_cache/"):
            self.assertIn(item, ignore)

    def test_no_product_packages_exist_in_task1(self) -> None:
        forbidden = [ROOT / "crates", ROOT / "python" / "gs_eval_adapters", ROOT / "src"]
        self.assertEqual([str(path.relative_to(ROOT)) for path in forbidden if path.exists()], [])


if __name__ == "__main__":
    unittest.main()
