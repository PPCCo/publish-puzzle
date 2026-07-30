from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .errors import BuildError
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, sha256_file, slugify, utc_now


def _find_latest(project_dir: Path, patterns: list[str]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(path for path in project_dir.glob(pattern) if path.is_file())
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def _copy(source: Path | None, target: Path, issues: list[str], label: str, required: bool = True) -> str | None:
    if source is None or not source.exists():
        if required:
            issues.append(f"Missing required {label}")
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target.as_posix()


def _canonical_metadata(paths: ProjectPaths) -> dict[str, Any]:
    metadata_path = paths.directory / "metadata" / "book.json"
    if not metadata_path.exists():
        raise BuildError("Missing canonical metadata: metadata/book.json")
    return load_json(metadata_path)


def _write_checksums(package_dir: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(package_dir.rglob("*")):
        if path.is_file() and path.name not in {"checksums.sha256", "package-manifest.json"}:
            records.append({"path": path.relative_to(package_dir).as_posix(), "sha256": sha256_file(path)})
    (package_dir / "checksums.sha256").write_text("".join(f"{item['sha256'].split(':',1)[1]}  {item['path']}\n" for item in records), encoding="utf-8")
    records.append({"path": "checksums.sha256", "sha256": sha256_file(package_dir / "checksums.sha256")})
    return records


def _common_manifest(paths: ProjectPaths, channel: str, metadata: dict[str, Any], package_dir: Path, issues: list[str], warnings: list[str]) -> dict[str, Any]:
    files = _write_checksums(package_dir)
    status = "fail" if issues else ("warning" if warnings else "pass")
    manifest = {
        "schema_version": "1.0",
        "project_id": paths.project_id,
        "channel": channel,
        "edition": int(metadata.get("edition", 1)),
        "created_at": utc_now(),
        "source_artifact_hashes": sorted(set(load_json(paths.state).get("active_artifacts", {}).values())),
        "files": [{"path": item["path"], "sha256": item["sha256"], "purpose": item["path"]} for item in files],
        "preflight_status": status,
        "issues": issues + warnings,
        "external_write_performed": False,
    }
    atomic_write_json(package_dir / "package-manifest.json", manifest)
    return manifest


def package_kdp(paths: ProjectPaths, metadata: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = ["Recheck current KDP requirements and upload manually; the base framework performs no KDP login or publication"]
    interior = _find_latest(paths.directory, ["outputs/interior/interior.pdf"])
    cover = _find_latest(paths.directory, ["outputs/cover/cover-wrap.pdf"])
    project = load_yaml(paths.config)
    formats = set(project.get("formats", []))
    if {"paperback", "hardcover"} & formats:
        _copy(interior, package_dir / "print" / "interior.pdf", issues, "print interior")
        _copy(cover, package_dir / "print" / "cover.pdf", issues, "print full cover")
    if {"digital-pdf"} & formats:
        digital = _find_latest(paths.directory, ["outputs/digital/printable.pdf"])
        _copy(digital, package_dir / "digital" / "printable.pdf", issues, "digital printable", required=False)
    listing = {
        "title": metadata.get("title"), "subtitle": metadata.get("subtitle"),
        "contributors": metadata.get("contributors", []), "language": metadata.get("language"),
        "description": metadata.get("description"), "keywords": metadata.get("keywords", []),
        "subjects": metadata.get("subjects", []), "audience": metadata.get("audience", {}),
        "edition": metadata.get("edition", 1), "rights_statement": metadata.get("rights_statement"),
        "pricing": metadata.get("pricing", {}), "identifiers": metadata.get("identifiers", []),
    }
    atomic_write_json(package_dir / "listing.json", listing)
    (package_dir / "description.md").write_text(str(metadata.get("description", "")) + "\n", encoding="utf-8")
    (package_dir / "keywords.txt").write_text("\n".join(metadata.get("keywords", [])) + "\n", encoding="utf-8")
    atomic_write_json(package_dir / "categories.json", {"subjects": metadata.get("subjects", []), "notice": "Map to current KDP categories during manual upload"})
    (package_dir / "upload-checklist.md").write_text("# KDP manual upload checklist\n\n- Recheck current official format, trim, bleed, cover, metadata, and AI-content disclosure requirements.\n- Inspect ebook in the current previewer.\n- Inspect paperback/hardcover preview and order a physical proof.\n- Confirm rights, territories, prices, tax/payment/account settings, and release authorization.\n- Record platform submission and publication evidence separately.\n", encoding="utf-8")
    return _common_manifest(paths, "kdp", metadata, package_dir, issues, warnings)


def _digital_files(paths: ProjectPaths, package_dir: Path, issues: list[str]) -> list[str]:
    """Copy the digital printable bundle / interior into the package."""
    copied: list[str] = []
    digital = _find_latest(paths.directory, ["outputs/digital/printable.pdf"])
    interior = _find_latest(paths.directory, ["outputs/interior/interior.pdf"])
    source = digital or interior
    if source:
        _copy(source, package_dir / "files" / "printable.pdf", issues, "printable PDF")
        copied.append("files/printable.pdf")
    else:
        issues.append("No digital printable or interior PDF found to sell")
    bundle_index = paths.directory / "outputs" / "digital" / "bundle-index.json"
    if bundle_index.exists():
        _copy(bundle_index, package_dir / "files" / "bundle-index.json", issues, "bundle index", required=False)
        copied.append("files/bundle-index.json")
    return copied


def package_etsy(paths: ProjectPaths, metadata: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = ["Etsy assets are prepared offline; the base framework performs no Etsy login, listing, or file upload"]
    _digital_files(paths, package_dir, issues)
    title = str(metadata.get("title", ""))
    listing = {
        "title": title,
        "description": metadata.get("description", ""),
        "tags": (metadata.get("keywords") or [])[:13],
        "materials": ["digital download", "printable PDF"],
        "type": "download",
        "who_made": "i_did",
        "is_supply": False,
        "when_made": "made_to_order",
        "price": metadata.get("pricing", {}).get("digital_price"),
        "currency": metadata.get("pricing", {}).get("currency", "USD"),
        "license": "personal-use-unless-otherwise-stated",
    }
    atomic_write_json(package_dir / "etsy-listing.json", listing)
    (package_dir / "listing-checklist.md").write_text(
        "# Etsy digital-listing checklist\n\n"
        "- Create a digital listing and upload preview images plus the print-ready files.\n"
        "- Paste title, description, and tags from etsy-listing.json.\n"
        "- Set instant-download delivery and confirm the commercial/personal-use license text.\n"
        "- Confirm shop policies, pricing, and file formats.\n"
        "- Publish only after recording a valid release authorization.\n",
        encoding="utf-8",
    )
    return _common_manifest(paths, "etsy", metadata, package_dir, issues, warnings)


def package_gumroad(paths: ProjectPaths, metadata: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = ["Gumroad assets are prepared offline; the base framework performs no Gumroad login or product creation"]
    _digital_files(paths, package_dir, issues)
    product = {
        "name": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "price": metadata.get("pricing", {}).get("digital_price"),
        "currency": metadata.get("pricing", {}).get("currency", "USD"),
        "tags": (metadata.get("keywords") or [])[:10],
        "license": "see-listing-terms",
    }
    atomic_write_json(package_dir / "gumroad-product.json", product)
    (package_dir / "listing-checklist.md").write_text(
        "# Gumroad product checklist\n\n"
        "- Create a product and upload the printable bundle.\n"
        "- Paste name, description, and pricing from gumroad-product.json.\n"
        "- Set license terms and any variant tiers.\n"
        "- Publish only after recording a valid release authorization.\n",
        encoding="utf-8",
    )
    return _common_manifest(paths, "gumroad", metadata, package_dir, issues, warnings)


def package_generic(paths: ProjectPaths, metadata: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    atomic_write_json(package_dir / "metadata.json", metadata)
    candidates = [
        _find_latest(paths.directory, ["outputs/interior/interior.pdf"]),
        _find_latest(paths.directory, ["outputs/cover/cover-wrap.pdf"]),
        _find_latest(paths.directory, ["outputs/digital/printable.pdf"]),
    ]
    for source in [x for x in candidates if x]:
        _copy(source, package_dir / "files" / source.name, issues, source.name, required=False)
    rights = paths.directory / "rights" / "gate-latest.json"
    if rights.exists():
        _copy(rights, package_dir / "rights-summary.json", issues, "rights summary", required=False)
    if not (package_dir / "files").exists():
        issues.append("No built format artifacts found")
    return _common_manifest(paths, "generic", metadata, package_dir, issues, warnings)


def package_channel(root: Path, project_id: str, channel: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    metadata = _canonical_metadata(paths)
    channel = channel.lower()
    package_dir = paths.directory / "outputs" / "packages" / channel
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    if channel == "kdp":
        manifest = package_kdp(paths, metadata, package_dir)
    elif channel == "etsy":
        manifest = package_etsy(paths, metadata, package_dir)
    elif channel == "gumroad":
        manifest = package_gumroad(paths, metadata, package_dir)
    elif channel == "generic":
        manifest = package_generic(paths, metadata, package_dir)
    else:
        raise BuildError(f"Unsupported channel: {channel}")
    from .artifacts import register_artifact
    artifact = register_artifact(
        root,
        project_id,
        package_dir / "package-manifest.json",
        f"platform-package-{slugify(channel)}",
        "PLATFORM_PACKAGING",
        f"package-{channel}",
        rights_status="not-applicable",
        validation_status=manifest["preflight_status"],
        provenance={"channel": channel, "source_artifact_hashes": manifest["source_artifact_hashes"]},
    )
    manifest["registered_artifact"] = {"artifact_id": artifact["artifact_id"], "sha256": artifact["sha256"]}
    return manifest
