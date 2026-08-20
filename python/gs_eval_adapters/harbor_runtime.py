from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from harbor.environments.docker.docker import (
    DockerEnvironment,
)
from harbor.models.task.config import EnvironmentConfig, NetworkMode
from harbor.models.trial.paths import TrialPaths

# Harbor 0.21.0 does not publish a py.typed marker; validate the adapter seam
# while treating its third-party implementation as an untyped runtime boundary.
# mypy: disable-error-code=import-untyped

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_DOCKER_IMAGE_REFERENCE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]+)?/)?"
    r"[a-z0-9](?:[a-z0-9._/-]*[a-z0-9])?@sha256:[0-9a-f]{64}$"
)


class GitSpaceHarborEnvironment(DockerEnvironment):
    """Harbor Docker environment with GitSpace-pinned runtime identities.

    Harbor resolves the task image and network policy from the task definition,
    while the job-level environment accepts only constructor kwargs. This
    adapter uses that supported extension point to bind the prebuilt task image
    and the egress-control sidecar before DockerEnvironment builds its compose
    plan. No unknown JobConfig fields are relied on.
    """

    def __init__(
        self,
        *,
        environment_dir: Path,
        environment_name: str,
        session_id: str,
        trial_paths: TrialPaths,
        task_env_config: EnvironmentConfig,
        gitspace_environment_image_ref: str,
        gitspace_environment_image_id: str,
        gitspace_egress_sidecar_image_ref: str,
        gitspace_egress_sidecar_image_id: str,
        **kwargs: Any,
    ) -> None:
        _validate_image_reference(
            gitspace_environment_image_ref,
            "gitspace_environment_image_ref",
        )
        if (
            gitspace_environment_image_ref.rsplit("@", 1)[1]
            != gitspace_environment_image_id
            or _DIGEST.fullmatch(gitspace_environment_image_id) is None
        ):
            raise ValueError("GitSpace environment image reference/id differ")
        _validate_image_reference(
            gitspace_egress_sidecar_image_ref,
            "gitspace_egress_sidecar_image_ref",
        )
        if (
            gitspace_egress_sidecar_image_ref.rsplit("@", 1)[1]
            != gitspace_egress_sidecar_image_id
            or _DIGEST.fullmatch(gitspace_egress_sidecar_image_id) is None
        ):
            raise ValueError("GitSpace sidecar image reference/id differ")
        if task_env_config.network_mode != NetworkMode.NO_NETWORK:
            raise ValueError("GitSpace Harbor environment requires no-network")

        resolved_task_env = task_env_config.model_copy(
            update={"docker_image": gitspace_environment_image_ref}
        )
        self.gitspace_environment_image_ref = gitspace_environment_image_ref
        self.gitspace_egress_sidecar_image_ref = gitspace_egress_sidecar_image_ref
        self.gitspace_egress_sidecar_image_id = gitspace_egress_sidecar_image_id
        super().__init__(
            environment_dir=environment_dir,
            environment_name=environment_name,
            session_id=session_id,
            trial_paths=trial_paths,
            task_env_config=resolved_task_env,
            **kwargs,
        )

    async def _ensure_egress_control_sidecar_image_built(self) -> None:
        """Bind the prequalified sidecar instead of building a mutable image."""

        self._env_vars.egress_control_sidecar_image_name = (
            self.gitspace_egress_sidecar_image_ref
        )


def _validate_image_reference(value: str, label: str) -> None:
    if type(value) is not str or _DOCKER_IMAGE_REFERENCE.fullmatch(value) is None:
        raise ValueError(f"{label} must be digest-bound")
    digest = value.rsplit("@", 1)[1]
    if _DIGEST.fullmatch(digest) is None:
        raise ValueError(f"{label} must end in a sha256 digest")
