#!/usr/bin/env python3
"""Install the checksum-pinned official Linux x86_64 CLI for unsigned CI builds."""
import hashlib
import io
from pathlib import Path
import platform
import shutil
import tarfile
import urllib.request

VERSION='1.6.0'
URL='https://releases.rive.app/cli/v1.6.0/rive-linux-x64.tar.gz'
SHA256='e9c00637ba9fc0e8a7594d04817b6c17a0e82e6647f3826fb9007fd803077566'
ROOT=Path(__file__).resolve().parents[1]


def install(destination):
    if platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64'):
        raise RuntimeError('CI requires a Linux x86_64 runner; other platforms should set RIVE_CLI manually.')
    with urllib.request.urlopen(URL,timeout=120) as response:
        archive=response.read()
    if hashlib.sha256(archive).hexdigest()!=SHA256:
        raise RuntimeError('Rive CLI download checksum mismatch; refusing to install.')
    # Read only this regular member: never extract the archive's path tree.
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as bundle:
        member=bundle.getmember('rive')
        if not member.isfile():
            raise RuntimeError('Expected a regular rive executable, not a link or directory.')
        destination.parent.mkdir(parents=True,exist_ok=True)
        with bundle.extractfile(member) as source, destination.open('wb') as target:
            shutil.copyfileobj(source,target)
    destination.chmod(0o755)
    print(f'Installed verified Rive CLI {VERSION}: {destination}')


if __name__=='__main__':
    install(ROOT/'.tooling'/'ci'/'rive')
