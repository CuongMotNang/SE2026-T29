from pathlib import Path

from scripts.release_manifest import ImageSpec, ReleaseManifest

VALID_DIGEST = "sha256:4b971a539b2b528a4be46313b29c926e838e55e42d765b26bf3b7a5a87be4e04"


def get_repo_root() -> Path:
    current = Path.cwd()
    if (current / "docs" / "releases" / "v0.1.0.json").exists():
        return current
    if (current.parent / "docs" / "releases" / "v0.1.0.json").exists():
        return current.parent
    return Path(__file__).resolve().parents[3]


def test_image_spec_validation_passes_valid_spec():
    spec = ImageSpec(
        repository="ghcr.io/cuongmotnang/booking-backend",
        tag="v0.1.0",
        digest=VALID_DIGEST,
    )
    errors = spec.validate("backend")
    assert errors == []
    assert spec.pinned_reference == f"ghcr.io/cuongmotnang/booking-backend@{VALID_DIGEST}"


def test_image_spec_rejects_latest_tag():
    spec = ImageSpec(
        repository="ghcr.io/cuongmotnang/booking-backend",
        tag="latest",
        digest=VALID_DIGEST,
    )
    errors = spec.validate("backend")
    assert any("forbidden tag 'latest'" in e for e in errors)


def test_image_spec_rejects_invalid_digest():
    spec = ImageSpec(
        repository="ghcr.io/cuongmotnang/booking-backend",
        tag="v0.1.0",
        digest="md5:invalidhex",
    )
    errors = spec.validate("backend")
    assert any("Must be in format 'sha256:<64-hex-characters>'" in e for e in errors)


def test_manifest_validation_passes():
    manifest = ReleaseManifest(
        release="v0.1.0",
        commit_sha="e0426ba69da49d4f2bd56718a0f7a6392d8dcae2",
        migration_revision="20261007_0001",
        images={
            "backend": ImageSpec(
                repository="ghcr.io/cuongmotnang/booking-backend",
                tag="v0.1.0",
                digest=VALID_DIGEST,
            )
        },
    )
    errors = manifest.validate()
    assert errors == []


def test_manifest_validation_rejects_latest_release():
    manifest = ReleaseManifest(
        release="latest",
        commit_sha="e0426ba69da49d4f2bd56718a0f7a6392d8dcae2",
        migration_revision="20261007_0001",
        images={
            "backend": ImageSpec(
                repository="ghcr.io/cuongmotnang/booking-backend",
                tag="v0.1.0",
                digest=VALID_DIGEST,
            )
        },
    )
    errors = manifest.validate()
    assert any("cannot be named 'latest'" in e for e in errors)


def test_manifest_validation_rejects_invalid_commit_sha():
    manifest = ReleaseManifest(
        release="v0.1.0",
        commit_sha="not-a-valid-sha!",
        migration_revision="20261007_0001",
        images={
            "backend": ImageSpec(
                repository="ghcr.io/cuongmotnang/booking-backend",
                tag="v0.1.0",
                digest=VALID_DIGEST,
            )
        },
    )
    errors = manifest.validate()
    assert any("Commit SHA" in e for e in errors)


def test_manifest_serialization_and_deserialization(tmp_path: Path):
    manifest = ReleaseManifest(
        release="v0.1.0",
        commit_sha="e0426ba69da49d4f2bd56718a0f7a6392d8dcae2",
        migration_revision="20261007_0001",
        images={
            "backend": ImageSpec(
                repository="ghcr.io/cuongmotnang/booking-backend",
                tag="v0.1.0",
                digest=VALID_DIGEST,
            )
        },
    )
    target_path = tmp_path / "test-manifest.json"
    manifest.save(target_path)

    loaded = ReleaseManifest.load(target_path)
    assert loaded.release == "v0.1.0"
    assert loaded.commit_sha == "e0426ba69da49d4f2bd56718a0f7a6392d8dcae2"
    assert loaded.migration_revision == "20261007_0001"
    assert "backend" in loaded.images
    assert loaded.images["backend"].digest == VALID_DIGEST


def test_v010_reference_manifest_file_is_valid():
    ref_path = get_repo_root() / "docs" / "releases" / "v0.1.0.json"
    assert ref_path.exists(), f"Reference manifest {ref_path} must exist"
    manifest = ReleaseManifest.load(ref_path)
    assert manifest.release == "v0.1.0"
    assert manifest.migration_revision == "20261007_0001"
    assert manifest.validate() == []
