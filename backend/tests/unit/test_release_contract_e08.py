from pathlib import Path

from fastapi.testclient import TestClient
from scripts.release_manifest import ReleaseManifest

from app.config import Settings, get_settings
from app.main import create_app


def get_repo_root() -> Path:
    current = Path.cwd()
    if (current / "docs" / "releases" / "v0.1.0.json").exists():
        return current
    if (current.parent / "docs" / "releases" / "v0.1.0.json").exists():
        return current.parent
    return Path(__file__).resolve().parents[3]


def test_e08_version_endpoint_matches_release_manifest():
    """E08 verification: /api/version matches release manifest parameters."""
    manifest_path = get_repo_root() / "docs" / "releases" / "v0.1.0.json"
    manifest = ReleaseManifest.load(manifest_path)

    # Configure application settings to reflect the manifest
    test_settings = Settings(
        release=manifest.release,
        commit_sha=manifest.commit_sha,
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings

    client = TestClient(app)
    response = client.get("/api/version")

    assert response.status_code == 200
    data = response.json()
    assert data["release"] == manifest.release
    assert data["commit_sha"] == manifest.commit_sha
    assert data["release"] != "latest", "Release must never be 'latest'"


def test_e08_release_manifest_traceability_to_image_spec():
    """E08 verification: Manifest binds release tag, commit SHA, and exact sha256 digest."""
    manifest_path = get_repo_root() / "docs" / "releases" / "v0.1.0.json"
    manifest = ReleaseManifest.load(manifest_path)

    backend_image = manifest.images["backend"]
    assert backend_image.digest.startswith("sha256:")
    assert len(backend_image.digest) == 71  # "sha256:" + 64 hex chars
    assert backend_image.tag == manifest.release
    assert backend_image.pinned_reference.endswith(backend_image.digest)
