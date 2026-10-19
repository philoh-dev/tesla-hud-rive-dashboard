"""Checksum installer safety checks, with no real network or CLI dependency."""
import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from ci import install_rive_cli as installer
from build import OUTPUT
from generate import ROOT


class CliInstallerTest(unittest.TestCase):
    def test_workflow_installs_linux_libraries_before_starting_cli(self):
        workflow=(ROOT/'.github/workflows/dashboard.yml').read_text()
        dependencies=workflow.index('name: Install Linux runtime libraries')
        startup=workflow.index('name: Install checksum-pinned Rive CLI')
        self.assertLess(dependencies,startup)
        for package in ('libegl1','libgles2','libx11-6','libwayland-client0',
                        'libwayland-egl1','libxkbcommon0','libstdc++6','zlib1g'):
            self.assertIn(package,workflow[dependencies:startup])

    def test_named_design_export_is_in_dashboard_directory(self):
        self.assertEqual(OUTPUT.relative_to(ROOT).as_posix(),
                         'dashboard/model-y-juniper-stealth-grey.riv')

    def archive(self,link=False):
        output=io.BytesIO()
        with tarfile.open(fileobj=output,mode='w:gz') as bundle:
            member=tarfile.TarInfo('rive')
            if link:
                member.type=tarfile.SYMTYPE
                member.linkname='/outside'
                bundle.addfile(member)
            else:
                member.size=4
                bundle.addfile(member,io.BytesIO(b'rive'))
            unrelated=tarfile.TarInfo('../must-not-extract')
            unrelated.size=1
            bundle.addfile(unrelated,io.BytesIO(b'x'))
        return output.getvalue()

    def run_install(self,archive,destination,checksum=None):
        with patch.object(installer.platform,'system',return_value='Linux'), \
             patch.object(installer.platform,'machine',return_value='x86_64'), \
             patch.object(installer.urllib.request,'urlopen',return_value=io.BytesIO(archive)), \
             patch.object(installer,'SHA256',checksum or hashlib.sha256(archive).hexdigest()):
            installer.install(destination)

    def test_installs_only_verified_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)/'bin'/'rive'
            self.run_install(self.archive(),destination)
            self.assertEqual(destination.read_bytes(),b'rive')
            self.assertEqual(destination.stat().st_mode&0o777,0o755)
            self.assertEqual(list(destination.parent.iterdir()),[destination])

    def test_rejects_checksum_mismatch_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)/'rive'
            with self.assertRaisesRegex(RuntimeError,'checksum mismatch'):
                self.run_install(self.archive(),destination,'0'*64)
            self.assertFalse(destination.exists())

    def test_rejects_symlink_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)/'rive'
            with self.assertRaisesRegex(RuntimeError,'regular rive executable'):
                self.run_install(self.archive(link=True),destination)
            self.assertFalse(destination.exists())

    def test_rejects_unsupported_runner_before_download(self):
        with patch.object(installer.platform,'system',return_value='Linux'), \
             patch.object(installer.platform,'machine',return_value='aarch64'), \
             patch.object(installer.urllib.request,'urlopen') as download:
            with self.assertRaisesRegex(RuntimeError,'x86_64'):
                installer.install(Path('unused'))
            download.assert_not_called()


if __name__=='__main__':
    unittest.main()
