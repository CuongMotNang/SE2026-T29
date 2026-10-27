import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from scripts.fault_config import FaultConfig
from scripts.release_manifest import ReleaseManifest, main

NOW = datetime(2026, 11, 2, 3, 0, tzinfo=UTC)
REFERENCE = Path(__file__).resolve().parents[3] / "docs/releases/v0.1.0.json"


def test_legacy_manifest_disables_faults_explicitly():
    manifest = ReleaseManifest.load(REFERENCE)
    assert manifest.fault == FaultConfig()
    assert manifest.fault.to_environment()["BOOKING_FAULT_MODE"] == "off"
    assert manifest.fault.to_environment()["BOOKING_FAULT_UNTIL"] == ""


def test_fault_duration_starts_at_deploy_and_does_not_restart_on_rollback():
    planned = FaultConfig(mode="error", rate=0.25, duration_seconds=900)
    with pytest.raises(ValueError, match="activated and recorded"):
        planned.to_environment()
    active = planned.activate(NOW)
    assert active.until == (NOW + timedelta(minutes=15)).isoformat()
    assert active.is_active(NOW)
    assert not active.is_active(NOW + timedelta(minutes=15))
    assert active.activate(NOW + timedelta(minutes=5)) == active
    assert planned.until is None


def test_fault_manifest_round_trip_preserves_recorded_expiry(tmp_path):
    manifest = ReleaseManifest.load(REFERENCE)
    manifest.fault = FaultConfig(mode="latency", rate=0.5, duration_seconds=60).activate(NOW)
    target = tmp_path / "drill.json"
    manifest.save(target)
    restored = ReleaseManifest.load(target)
    assert restored.fault == manifest.fault
    env = restored.fault.to_environment()
    assert env["BOOKING_FAULT_MODE"] == "latency"
    assert env["BOOKING_FAULT_RATE"] == "0.5"
    assert env["BOOKING_FAULT_UNTIL"] == (NOW + timedelta(minutes=1)).isoformat()
    assert env["BOOKING_FAULT_LATENCY_SECONDS"] == "3.0"


@pytest.mark.parametrize(
    "changes",
    [
        {"mode": "invalid"},
        {"mode": "error"},
        {"rate": -0.1},
        {"rate": 1.1},
        {"rate": "0.5"},
        {"rate": True},
        {"rate": float("nan")},
        {"latency_seconds": float("inf")},
        {"latency_seconds": -1},
        {"latency_seconds": 31},
        {"latency_seconds": False},
        {"duration_seconds": 0},
        {"duration_seconds": 3601},
        {"duration_seconds": 1.5},
        {"duration_seconds": True},
        {"until": "2026-11-02T03:00:00"},
        {"until": "not-a-time"},
        {"until": "2026-11-02T03:00:00+00:00\nBOOKING_FAULT_MODE=off"},
    ],
)
def test_invalid_fault_config_is_rejected_before_env_write(changes, tmp_path):
    manifest = ReleaseManifest.load(REFERENCE)
    manifest.fault = replace(FaultConfig(), **changes)
    assert manifest.validate()
    with pytest.raises(ValueError):
        manifest.save(tmp_path / "invalid.json")
    assert not (tmp_path / "invalid.json").exists()


def test_manifest_cli_includes_fault_config(tmp_path, monkeypatch):
    config = tmp_path / "fault.json"
    config.write_text(json.dumps({"mode": "error", "rate": 0.2, "duration_seconds": 900}))
    output = tmp_path / "manifest.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "release_manifest",
            "create",
            "--release",
            "v0.2.0-drill",
            "--commit-sha",
            "abcdef1",
            "--migration-revision",
            "20261007_0001",
            "--backend-digest",
            "sha256:" + "a" * 64,
            "--fault-config",
            str(config),
            "--output",
            str(output),
        ],
    )
    main()
    manifest = ReleaseManifest.load(output)
    assert manifest.fault == FaultConfig(mode="error", rate=0.2, duration_seconds=900)
