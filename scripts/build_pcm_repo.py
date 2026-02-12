#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


REPOSITORY_SCHEMA = (
    "https://gitlab.com/kicad/code/kicad/-/raw/master/"
    "kicad/pcm/schemas/pcm.v1.schema.json#/definitions/Repository"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_zip_from_dir(source_dir: Path, out_zip: Path) -> None:
    with ZipFile(out_zip, "w", compression=ZIP_DEFLATED) as zf:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.relative_to(source_dir))


def dir_total_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build KiCad PCM package zip and repository index files."
    )
    parser.add_argument("--version", required=True, help="Package version, e.g. 1.0.0")
    parser.add_argument("--github-owner", required=True, help="GitHub username/org")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument(
        "--status",
        default="stable",
        choices=["stable", "testing", "development", "deprecated"],
        help="PCM version status",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    lib_content = root / "lib-content"
    metadata_base_path = root / "pcm" / "metadata.base.json"
    dist_dir = root / "dist"
    releases_dir = dist_dir / "releases"

    metadata_base = json.loads(metadata_base_path.read_text(encoding="utf-8"))
    identifier = metadata_base["identifier"]
    kicad_version = metadata_base.pop("kicad_version", "8.0")

    package_filename = f"{identifier}_v{args.version}_pcm.zip"
    release_url = (
        f"https://github.com/{args.github_owner}/{args.repo}/releases/download/"
        f"v{args.version}/{package_filename}"
    )

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    releases_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pcm-build-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        stage_dir = temp_dir / "package-root"
        shutil.copytree(lib_content, stage_dir)

        install_size = dir_total_size(stage_dir)
        metadata = dict(metadata_base)
        metadata["versions"] = [
            {
                "version": args.version,
                "status": args.status,
                "kicad_version": kicad_version,
            }
        ]

        metadata_in_package = dict(metadata)
        (stage_dir / "metadata.json").write_text(
            json.dumps(metadata_in_package, indent=2) + "\n",
            encoding="utf-8",
        )

        package_zip_path = releases_dir / package_filename
        write_zip_from_dir(stage_dir, package_zip_path)

    download_size = package_zip_path.stat().st_size
    download_sha = sha256_file(package_zip_path)

    metadata["versions"][0].update(
        {
            "download_sha256": download_sha,
            "download_url": release_url,
            "download_size": download_size,
            "install_size": install_size,
        }
    )

    packages_json = {"packages": [metadata]}
    packages_path = dist_dir / "packages.json"
    packages_path.write_text(json.dumps(packages_json, indent=2) + "\n", encoding="utf-8")

    resources_path = dist_dir / "resources.zip"
    with ZipFile(resources_path, "w", compression=ZIP_DEFLATED):
        pass

    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    update_time_utc = now.strftime("%Y-%m-%d %H:%M:%S")

    packages_url = (
        f"https://raw.githubusercontent.com/{args.github_owner}/{args.repo}/main/dist/packages.json"
    )
    resources_url = (
        f"https://raw.githubusercontent.com/{args.github_owner}/{args.repo}/main/dist/resources.zip"
    )
    repository = {
        "$schema": REPOSITORY_SCHEMA,
        "name": f"{args.repo} PCM repository",
        "maintainer": metadata.get("maintainer", metadata["author"]),
        "packages": {
            "url": packages_url,
            "sha256": sha256_file(packages_path),
            "update_time_utc": update_time_utc,
            "update_timestamp": timestamp,
        },
        "resources": {
            "url": resources_url,
            "sha256": sha256_file(resources_path),
            "update_time_utc": update_time_utc,
            "update_timestamp": timestamp,
        },
    }

    repository_path = dist_dir / "repository.json"
    repository_path.write_text(json.dumps(repository, indent=2) + "\n", encoding="utf-8")

    print(f"Built package: {package_zip_path}")
    print(f"Repository URL for KiCad PCM:")
    print(
        f"https://raw.githubusercontent.com/{args.github_owner}/{args.repo}/main/dist/repository.json"
    )


if __name__ == "__main__":
    main()
