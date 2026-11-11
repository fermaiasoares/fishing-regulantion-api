"""Download the IBGE BHB250 level-2 archive and print its provenance."""

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile

SOURCE_URL = (
    "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
    "bacias_e_divisoes_hidrograficas_do_brasil/2021/"
    "Bacias_Hidrograficas_do_Brasil_BHB250/vetores/bacias_nivel_2.zip"
)


def acquire(destination: Path, expected_sha256: str | None = None) -> dict:
    """Store a verified archive, preserving the destination on download failure."""
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("Expected SHA-256 must be 64 lowercase hexadecimal digits")

    checksum = hashlib.sha256()
    size_bytes = 0
    with urlopen(SOURCE_URL, timeout=60) as response:
        with NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
            archive = Path(temporary.name)
            try:
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
                    checksum.update(chunk)
                    size_bytes += len(chunk)
                temporary.close()

                sha256 = checksum.hexdigest()
                if expected_sha256 is not None and sha256 != expected_sha256:
                    raise ValueError(f"SHA-256 mismatch: expected {expected_sha256}, got {sha256}")
                with ZipFile(archive) as source:
                    if not source.infolist():
                        raise ValueError("IBGE archive is empty")

                archive.replace(destination)
            finally:
                archive.unlink(missing_ok=True)

    return {
        "dataset_slug": "ibge-bhb250-level-2",
        "version": "2021",
        "publisher": "IBGE",
        "source_url": SOURCE_URL,
        "collected_at": datetime.now(UTC).isoformat(),
        "documented_source_crs": "EPSG:4674",
        "checksum_sha256": sha256,
        "size_bytes": size_bytes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="ZIP path in an existing directory")
    parser.add_argument("--expected-sha256", help="SHA-256 from an earlier acquisition")
    args = parser.parse_args()

    try:
        provenance = acquire(args.destination, args.expected_sha256)
    except (BadZipFile, OSError, ValueError) as error:
        parser.exit(1, f"IBGE download failed: {error}\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
