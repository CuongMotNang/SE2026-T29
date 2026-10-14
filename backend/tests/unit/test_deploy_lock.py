from pathlib import Path

import pytest
from scripts.deploy_lock import DeploymentLock, DeploymentLockError, LockMetadata


def test_deploy_lock_acquire_and_release(tmp_path: Path):
    lock_path = tmp_path / "test.lock"
    lock = DeploymentLock(lock_dir=lock_path, operation="test_op")

    assert not lock_path.exists()
    lock.acquire()
    assert lock_path.exists()
    assert (lock_path / "lock_metadata.json").exists()
    assert lock.is_acquired

    lock.release()
    assert not lock_path.exists()
    assert not lock.is_acquired


def test_deploy_lock_context_manager(tmp_path: Path):
    lock_path = tmp_path / "test_cm.lock"
    with DeploymentLock(lock_dir=lock_path, operation="context_test") as lock:
        assert lock.is_acquired
        assert lock_path.exists()

    assert not lock_path.exists()
    assert not lock.is_acquired


def test_deploy_lock_mutual_exclusion(tmp_path: Path):
    lock_path = tmp_path / "test_mutex.lock"
    lock1 = DeploymentLock(lock_dir=lock_path, operation="deploy_1")
    lock1.acquire()

    lock2 = DeploymentLock(lock_dir=lock_path, operation="deploy_2", timeout_seconds=0.1)
    with pytest.raises(DeploymentLockError) as exc_info:
        lock2.acquire()

    assert "Cannot acquire deployment lock" in str(exc_info.value)
    assert "Concurrent deployments are forbidden" in str(exc_info.value)

    lock1.release()

    # Now lock2 should be able to acquire
    lock2.acquire()
    assert lock2.is_acquired
    lock2.release()


def test_deploy_lock_stale_lock_cleanup(tmp_path: Path):
    lock_path = tmp_path / "test_stale.lock"
    lock_path.mkdir(parents=True, exist_ok=True)

    # Write metadata with non-existent PID
    fake_meta = LockMetadata(
        pid=99999999,  # Non-existent PID
        operation="crashed_deploy",
        acquired_at="2026-01-01T00:00:00Z",
    )
    (lock_path / "lock_metadata.json").write_text(fake_meta.to_json(), encoding="utf-8")

    # A new deployer should detect dead PID, clean it up, and acquire successfully
    new_lock = DeploymentLock(lock_dir=lock_path, operation="recovery_deploy")
    new_lock.acquire()
    assert new_lock.is_acquired

    meta = LockMetadata.from_json((lock_path / "lock_metadata.json").read_text(encoding="utf-8"))
    assert meta.operation == "recovery_deploy"
    new_lock.release()
