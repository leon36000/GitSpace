from __future__ import annotations

import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


VERIFIER_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "terminal-bench-2.1-regex-log"
    / "tests"
    / "run_test.py"
)


def _load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "gitspace_normalized_verifier", VERIFIER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load normalized verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NormalizedVerifierTests(unittest.TestCase):
    def _run(self, source: str) -> tuple[int, bytes | None, bytes | None]:
        module = _load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "test_outputs.py"
            reward_path = root / "logs" / "reward.json"
            result_path = root / "logs" / "gitspace-result.json"
            source_path.write_text(source, encoding="utf-8")
            code = module.run_verifier(
                workspace_root=Path.cwd(),
                test_source=source_path,
                reward_path=reward_path,
                result_path=result_path,
            )
            reward = reward_path.read_bytes() if reward_path.exists() else None
            result = result_path.read_bytes() if result_path.exists() else None
            return code, reward, result

    def test_pass_writes_one_reward_and_functional_result(self) -> None:
        code, reward, result = self._run(
            "def test_regex_matches_dates():\n    return None\n"
        )

        self.assertEqual(code, 0)
        self.assertEqual(reward, b'{"reward":1}\n')
        self.assertIsNotNone(result)
        result_value = json.loads(result)
        self.assertEqual(result_value["kind"], "functional_pass")
        self.assertIsNone(result_value["exception_type_or_null"])

    def test_assertion_writes_zero_reward_and_functional_result(self) -> None:
        code, reward, result = self._run(
            "def test_regex_matches_dates():\n    raise AssertionError('wrong')\n"
        )

        self.assertEqual(code, 0)
        self.assertEqual(reward, b'{"reward":0}\n')
        self.assertIsNotNone(result)
        result_value = json.loads(result)
        self.assertEqual(result_value["kind"], "functional_assertion")
        self.assertEqual(result_value["exception_type_or_null"], "AssertionError")

    def test_non_assertion_exception_writes_infra_without_reward(self) -> None:
        code, reward, result = self._run(
            "def test_regex_matches_dates():\n    raise RuntimeError('harness')\n"
        )

        self.assertEqual(code, 70)
        self.assertIsNone(reward)
        self.assertIsNotNone(result)
        result_value = json.loads(result)
        self.assertEqual(result_value["kind"], "harness_infra")
        self.assertEqual(result_value["exception_type_or_null"], "RuntimeError")

    def test_preexisting_reward_is_infra_and_is_not_overwritten(self) -> None:
        module = _load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "test_outputs.py"
            reward_path = root / "logs" / "reward.json"
            result_path = root / "logs" / "gitspace-result.json"
            source_path.write_text(
                "def test_regex_matches_dates():\n    return None\n",
                encoding="utf-8",
            )
            reward_path.parent.mkdir()
            reward_path.write_bytes(b"sentinel")

            code = module.run_verifier(
                workspace_root=Path.cwd(),
                test_source=source_path,
                reward_path=reward_path,
                result_path=result_path,
            )

            self.assertEqual(code, 70)
            self.assertEqual(reward_path.read_bytes(), b"sentinel")
            self.assertEqual(
                json.loads(result_path.read_bytes())["kind"], "harness_infra"
            )

    def test_outputs_are_host_readable_on_rootless_workers(self) -> None:
        module = _load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "test_outputs.py"
            reward_path = root / "logs" / "reward.json"
            result_path = root / "logs" / "gitspace-result.json"
            source_path.write_text(
                "def test_regex_matches_dates():\n    return None\n",
                encoding="utf-8",
            )

            code = module.run_verifier(
                workspace_root=Path.cwd(),
                test_source=source_path,
                reward_path=reward_path,
                result_path=result_path,
            )

            self.assertEqual(code, 0)
            self.assertEqual(
                stat.S_IMODE(reward_path.stat().st_mode),
                0o644,
            )
            self.assertEqual(
                stat.S_IMODE(result_path.stat().st_mode),
                0o644,
            )


if __name__ == "__main__":
    unittest.main()
