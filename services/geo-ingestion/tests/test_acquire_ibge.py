import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import BadZipFile, ZipFile

from acquire_ibge import SOURCE_URL, acquire


class AcquisitionTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.destination = Path(directory.name) / "bacias.zip"

        data = io.BytesIO()
        with ZipFile(data, "w") as archive:
            archive.writestr("sample.txt", "local fixture")
        self.zip_bytes = data.getvalue()

    def test_acquires_and_records_exact_bytes(self):
        checksum = hashlib.sha256(self.zip_bytes).hexdigest()
        with patch("acquire_ibge.urlopen", return_value=io.BytesIO(self.zip_bytes)) as request:
            result = acquire(self.destination, checksum)

        request.assert_called_once_with(SOURCE_URL, timeout=60)
        self.assertEqual(self.destination.read_bytes(), self.zip_bytes)
        self.assertEqual(result["source_url"], SOURCE_URL)
        self.assertEqual(result["checksum_sha256"], checksum)
        self.assertEqual(result["size_bytes"], len(self.zip_bytes))
        self.assertTrue(result["collected_at"].endswith("+00:00"))

    def test_checksum_mismatch_preserves_previous_file(self):
        self.destination.write_bytes(b"previous archive")
        with patch("acquire_ibge.urlopen", return_value=io.BytesIO(self.zip_bytes)):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                acquire(self.destination, "0" * 64)

        self.assertEqual(self.destination.read_bytes(), b"previous archive")
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_non_zip_response_leaves_no_artifact(self):
        with patch("acquire_ibge.urlopen", return_value=io.BytesIO(b"<html>error</html>")):
            with self.assertRaises(BadZipFile):
                acquire(self.destination)

        self.assertEqual(list(self.destination.parent.iterdir()), [])

    def test_invalid_checksum_fails_before_network_request(self):
        with patch("acquire_ibge.urlopen") as request:
            with self.assertRaisesRegex(ValueError, "64 lowercase hexadecimal"):
                acquire(self.destination, "invalid")

        request.assert_not_called()
