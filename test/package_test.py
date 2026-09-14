import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
spec=importlib.util.spec_from_file_location('packager',Path(__file__).parents[1]/'tools/package_release.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PackageTests(unittest.TestCase):
    def test_reproducible_complete_package_without_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);p=m.package(out);first=p.read_bytes();m.package(out)
            self.assertEqual(first,p.read_bytes())
            self.assertIn(hashlib.sha256(first).hexdigest(),(out/'SHA256SUMS').read_text())
            with zipfile.ZipFile(p) as z:
                self.assertTrue({'KindleDash.koplugin/main.lua','KindleDash.koplugin/sha256.lua'} <= set(z.namelist()))
                self.assertFalse(any('settings' in n or 'quotas.json' in n for n in z.namelist()))
