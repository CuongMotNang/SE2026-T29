from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.deploy import Deployer
from scripts.release_manifest import ImageSpec, ReleaseManifest
from scripts.rollback import Rollbacker
from scripts.smoke_test import SmokeTestResult, SmokeTestRunner

DIGEST_V1 = "sha256:1111111111111111111111111111111111111111111111111111111111111111"
DIGEST_V2 = "sha256:2222222222222222222222222222222222222222222222222222222222222222"


@pytest.fixture
def v1_manifest(tmp_path: Path) -> Path:
    manifest = ReleaseManifest(
        release="v0.1.0",
        commit_sha="1111111111111111111111111111111111111111",
        migration_revision="20261007_0001",
        images={
            "backend": ImageSpec(
                repository="ghcr.io/cuongmotnang/booking-backend",
                tag="v0.1.0",
                digest=DIGEST_V1,
            )
        },
    )
    p = tmp_path / "v0.1.0.json"
    manifest.save(p)
    return p


@pytest.fixture
def v2_manifest(tmp_path: Path) -> Path:
    manifest = ReleaseManifest(
        release="v0.2.0",
        commit_sha="2222222222222222222222222222222222222222",
        migration_revision="20261007_0001",
        images={
            "backend": ImageSpec(
                repository="ghcr.io/cuongmotnang/booking-backend",
                tag="v0.2.0",
                digest=DIGEST_V2,
            )
        },
    )
    p = tmp_path / "v0.2.0.json"
    manifest.save(p)
    return p


def test_deployer_prepares_pinned_env_file(tmp_path: Path, v1_manifest: Path):
    deploy_state = tmp_path / "deploy"
    deployer = Deployer(
        manifest_path=v1_manifest,
        state_dir=deploy_state,
        dry_run=False,
        skip_container_ops=True,
    )
    manifest = ReleaseManifest.load(v1_manifest)
    deployer.prepare_environment_file(manifest)

    env_file = deploy_state / ".env.production"
    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")
    assert f"BACKEND_IMAGE_REF=ghcr.io/cuongmotnang/booking-backend@{DIGEST_V1}" in content
    assert "BOOKING_RELEASE=v0.1.0" in content
    assert "BOOKING_COMMIT_SHA=1111111111111111111111111111111111111111" in content


def test_deploy_and_rollback_manifest_history_flow(
    tmp_path: Path, v1_manifest: Path, v2_manifest: Path
):
    deploy_state = tmp_path / "deploy"

    # Step 1: Deploy v0.1.0 successfully
    deployer_v1 = Deployer(
        manifest_path=v1_manifest,
        state_dir=deploy_state,
        skip_container_ops=True,
    )
    deployer_v1.run()

    current_mf = deploy_state / "current-manifest.json"
    assert current_mf.exists()
    assert ReleaseManifest.load(current_mf).release == "v0.1.0"

    # Step 2: Deploy v0.2.0 successfully
    deployer_v2 = Deployer(
        manifest_path=v2_manifest,
        state_dir=deploy_state,
        skip_container_ops=True,
    )
    deployer_v2.run()

    previous_mf = deploy_state / "previous-manifest.json"
    assert previous_mf.exists()
    assert ReleaseManifest.load(previous_mf).release == "v0.1.0"
    assert ReleaseManifest.load(current_mf).release == "v0.2.0"

    # Step 3: Trigger rollback to previous manifest
    rollbacker = Rollbacker(
        target_manifest=previous_mf,
        state_dir=deploy_state,
        skip_container_ops=True,
    )
    rollbacker.run()

    # Current manifest should now be restored to v0.1.0
    assert ReleaseManifest.load(current_mf).release == "v0.1.0"
    env_content = (deploy_state / ".env.production").read_text(encoding="utf-8")
    assert "BOOKING_RELEASE=v0.1.0" in env_content
    assert f"@{DIGEST_V1}" in env_content


def test_deploy_auto_rollbacks_on_smoke_test_failure(
    tmp_path: Path, v1_manifest: Path, v2_manifest: Path
):
    deploy_state = tmp_path / "deploy"

    # Deploy initial good release v0.1.0
    deployer_v1 = Deployer(
        manifest_path=v1_manifest,
        state_dir=deploy_state,
        skip_container_ops=True,
    )
    deployer_v1.run()

    # Now attempt deploying v0.2.0, but simulate smoke test failure
    deployer_v2 = Deployer(
        manifest_path=v2_manifest,
        state_dir=deploy_state,
        skip_container_ops=False,  # Runs smoke tests
    )

    failed_result = [
        SmokeTestResult(
            success=False,
            step="readiness_check",
            duration_seconds=5.0,
            message="Readiness timed out",
            details={},
        )
    ]
    recovered_result = [
        SmokeTestResult(
            success=True,
            step="readiness_check",
            duration_seconds=1.0,
            message="Readiness ok",
            details={},
        ),
        SmokeTestResult(
            success=True,
            step="version_check",
            duration_seconds=0.5,
            message="Version ok",
            details={},
        ),
        SmokeTestResult(
            success=True,
            step="business_flow",
            duration_seconds=1.5,
            message="Flow ok",
            details={},
        ),
    ]

    # First call fails (deploy v2), second call succeeds (rollback to v1)
    with patch.object(SmokeTestRunner, "run_all", side_effect=[failed_result, recovered_result]):
        with patch.object(deployer_v2, "apply_migrations", MagicMock()):
            with patch.object(deployer_v2, "deploy_containers", MagicMock()):
                with patch.object(Rollbacker, "recreate_containers", MagicMock()):
                    with pytest.raises(RuntimeError) as exc_info:
                        deployer_v2.run()

    assert "Automatic rollback executed" in str(exc_info.value)

    # Verify state was safely rolled back to v0.1.0
    current_mf = deploy_state / "current-manifest.json"
    assert ReleaseManifest.load(current_mf).release == "v0.1.0"
