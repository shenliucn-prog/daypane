#!/usr/bin/env python3
"""Build reproducible plugin ZIP and checksums; never bundle local settings."""
import hashlib
from pathlib import Path
import zipfile

VERSION = '0.3.0'

def package(output=Path('dist')):
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(Path('KindleDash.koplugin').glob('*.lua'))
    files += [Path(p) for p in ('README.md','README.zh-CN.md','docs/UPGRADE.md','docs/UPGRADE.zh-CN.md','CHANGELOG.md')]
    target=output / f'ShawnKanban-{VERSION}.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info=zipfile.ZipInfo(str(path).replace('\\','/'), (2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644 << 16
            archive.writestr(info,path.read_bytes())
    (output/'SHA256SUMS').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    return target

if __name__=='__main__': print(package())
