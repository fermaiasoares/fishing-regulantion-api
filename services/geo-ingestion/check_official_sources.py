"""Check official hydrography downloads for the GitHub Actions smoke test."""

import argparse
import hashlib
import json
import re
import struct
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile

from acquire_ibge import acquire

ANA_LAYER = (
    "https://portal1.snirh.gov.br/server/rest/services/Hosted/"
    "main_geoft_bho6_trecho_drenagem/FeatureServer/0"
)
CARATINGA_ENVELOPE = "-42.20,-19.85,-42.05,-19.70"
SAMPLE_LIMIT = 10


def check_ibge(directory: Path) -> dict:
    destination = directory / "bacias.zip"
    provenance = acquire(destination)
    with destination.open("rb") as downloaded:
        checksum = hashlib.file_digest(downloaded, "sha256").hexdigest()
    if checksum != provenance["checksum_sha256"]:
        raise ValueError("IBGE archive SHA-256 differs from the acquisition report")

    with ZipFile(destination) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"IBGE archive has a corrupt member: {bad_member}")

        shapefiles = [name for name in archive.namelist() if name.lower().endswith(".shp")]
        if len(shapefiles) != 1:
            raise ValueError(f"Expected one IBGE shapefile, found {len(shapefiles)}")

        layer = shapefiles[0]
        stem = layer[:-4]
        members = {name.lower(): name for name in archive.namelist()}
        for extension in (".shx", ".dbf", ".prj"):
            if (stem + extension).lower() not in members:
                raise ValueError(f"Missing IBGE shapefile component {extension}")

        crs = archive.read(members[(stem + ".prj").lower()]).decode("ascii")
        if "SIRGAS2000" not in re.sub(r"[^A-Z0-9]", "", crs.upper()):
            raise ValueError("IBGE projection file does not declare SIRGAS 2000")

        with archive.open(members[(stem + ".dbf").lower()]) as attributes:
            header = attributes.read(8)
        if len(header) != 8:
            raise ValueError("Incomplete IBGE attribute table header")

        feature_count = struct.unpack_from("<I", header, 4)[0]
        if feature_count == 0:
            raise ValueError("IBGE shapefile has no records")

    return {**provenance, "shapefile": layer, "feature_count": feature_count}


def check_ana(directory: Path) -> dict:
    params = {
        "f": "json",
        "where": "1=1",
        "geometry": CARATINGA_ENVELOPE,
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outSR": 4326,
        "outFields": "fid,drn_pk,cotrecho,dsversao",
        "orderByFields": "fid ASC",
        "returnGeometry": "true",
        "resultRecordCount": SAMPLE_LIMIT,
    }
    source_url = f"{ANA_LAYER}/query?{urlencode(params)}"
    with urlopen(source_url, timeout=60) as response:
        raw = response.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("ANA sample exceeds 5 MiB")

    sample = json.loads(raw)
    if "error" in sample:
        raise ValueError(f"ANA returned an ArcGIS error: {sample['error']}")
    if sample.get("geometryType") != "esriGeometryPolyline":
        raise ValueError("ANA did not return polylines")
    if sample.get("spatialReference", {}).get("wkid") != 4326:
        raise ValueError("ANA sample is missing the requested EPSG:4326")

    features = sample.get("features", [])
    if not 1 <= len(features) <= SAMPLE_LIMIT:
        raise ValueError(f"Expected 1 to {SAMPLE_LIMIT} ANA features, got {len(features)}")

    ids = set()
    for feature in features:
        feature_id = feature.get("attributes", {}).get("fid")
        if type(feature_id) is not int or feature_id in ids:
            raise ValueError(f"Invalid or duplicate ANA feature ID: {feature_id}")
        ids.add(feature_id)
        paths = (feature.get("geometry") or {}).get("paths", [])
        if not paths or any(len(path) < 2 for path in paths):
            raise ValueError(f"ANA feature {feature_id} has an empty or incomplete line")
        for path in paths:
            for point in path:
                if len(point) != 2 or not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
                    raise ValueError(f"ANA feature {feature_id} has invalid WGS 84 coordinates")

    (directory / "ana-sample.json").write_bytes(raw)
    return {
        "publisher": "ANA",
        "dataset": "BHO6",
        "source_url": source_url,
        "collected_at": datetime.now(UTC).isoformat(),
        "sample_envelope": CARATINGA_ENVELOPE,
        "response_crs": "EPSG:4326",
        "checksum_sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "feature_count": len(features),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("ibge", "ana"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    check_source = {"ibge": check_ibge, "ana": check_ana}[args.source]
    try:
        args.directory.mkdir(parents=True, exist_ok=True)
        report = check_source(args.directory)
        report_json = json.dumps(report, indent=2)
        (args.directory / f"{args.source}-report.json").write_text(report_json + "\n", encoding="utf-8")
    except (BadZipFile, OSError, ValueError) as error:
        parser.exit(1, f"{args.source.upper()} source check failed: {error}\n")
    print(report_json)


if __name__ == "__main__":
    main()
