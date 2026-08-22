from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from gs_eval_adapters.harbor_runtime import GitSpaceHarborEnvironment
from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import EnvironmentConfig, NetworkMode

ENVIRONMENT_IMAGE_REF = "registry.invalid/gitspace/regex-log@sha256:" + "e" * 64
ENVIRONMENT_IMAGE_ID = "sha256:" + "e" * 64
SIDECAR_IMAGE_REF = "registry.invalid/gitspace/harbor-egress@sha256:" + "f" * 64
SIDECAR_IMAGE_ID = "sha256:" + "f" * 64


class HarborRuntimeTests(unittest.TestCase):
    def test_supported_environment_kwargs_bind_prebuilt_images_without_docker(
        self,
    ) -> None:
        task_environment = EnvironmentConfig(network_mode=NetworkMode.NO_NETWORK)

        with patch.object(DockerEnvironment, "__init__", return_value=None) as init:
            environment = GitSpaceHarborEnvironment(
                environment_dir=Path("/fixture"),
                environment_name="regex-log",
                session_id="trial-1",
                trial_paths=None,  # type: ignore[arg-type]
                task_env_config=task_environment,
                gitspace_environment_image_ref=ENVIRONMENT_IMAGE_REF,
                gitspace_environment_image_id=ENVIRONMENT_IMAGE_ID,
                gitspace_egress_sidecar_image_ref=SIDECAR_IMAGE_REF,
                gitspace_egress_sidecar_image_id=SIDECAR_IMAGE_ID,
            )

        resolved = init.call_args.kwargs["task_env_config"]
        self.assertEqual(resolved.docker_image, ENVIRONMENT_IMAGE_REF)
        environment._env_vars = SimpleNamespace(  # type: ignore[attr-defined]
            egress_control_sidecar_image_name=None
        )
        asyncio.run(environment._ensure_egress_control_sidecar_image_built())
        self.assertEqual(
            environment._env_vars.egress_control_sidecar_image_name,  # type: ignore[attr-defined]
            SIDECAR_IMAGE_REF,
        )

    def test_runtime_rejects_a_non_closed_task_network(self) -> None:
        task_environment = EnvironmentConfig(network_mode=NetworkMode.PUBLIC)

        with self.assertRaisesRegex(ValueError, "no-network"):
            GitSpaceHarborEnvironment(
                environment_dir=Path("/fixture"),
                environment_name="regex-log",
                session_id="trial-1",
                trial_paths=None,  # type: ignore[arg-type]
                task_env_config=task_environment,
                gitspace_environment_image_ref=ENVIRONMENT_IMAGE_REF,
                gitspace_environment_image_id=ENVIRONMENT_IMAGE_ID,
                gitspace_egress_sidecar_image_ref=SIDECAR_IMAGE_REF,
                gitspace_egress_sidecar_image_id=SIDECAR_IMAGE_ID,
            )

    def test_runtime_rejects_a_non_docker_image_reference(self) -> None:
        task_environment = EnvironmentConfig(network_mode=NetworkMode.NO_NETWORK)

        with self.assertRaisesRegex(ValueError, "digest-bound"):
            GitSpaceHarborEnvironment(
                environment_dir=Path("/fixture"),
                environment_name="regex-log",
                session_id="trial-1",
                trial_paths=None,  # type: ignore[arg-type]
                task_env_config=task_environment,
                gitspace_environment_image_ref=(
                    "local://gitspace/regex-log@sha256:" + "e" * 64
                ),
                gitspace_environment_image_id=ENVIRONMENT_IMAGE_ID,
                gitspace_egress_sidecar_image_ref=SIDECAR_IMAGE_REF,
                gitspace_egress_sidecar_image_id=SIDECAR_IMAGE_ID,
            )


if __name__ == "__main__":
    unittest.main()
