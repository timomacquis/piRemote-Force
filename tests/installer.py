"""Exercise the unmodified standard installer in a disposable fake systemd tree."""
from pathlib import Path
import tempfile,zipfile,subprocess,os
B=Path(__file__).resolve().parents[1];archive=B/'dist/0.1.0/piRemote-0.1.0-mpc-armv7.zip'
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp);system=tmp/'system';unit=system/'usr/lib/systemd/system/acvs.service';unit.parent.mkdir(parents=True)
    before='[Service]\nEnvironment=LD_PRELOAD=/data/other-existing-addin.so\n';unit.write_text(before)
    mounts=tmp/'mounts';mounts.write_text('/dev/mock / ext4 rw,relatime 0 0\n')
    log=tmp/'commands.log';dest=tmp/'installed/piremote';unpacked=tmp/'package'
    with zipfile.ZipFile(archive) as z:z.extractall(unpacked)
    folder=next(unpacked.iterdir())
    env=dict(os.environ,ADDIN_INSTALL_TEST='1',SYSTEMD_ROOT=str(system),ADDIN_TEST_LOG=str(log),ADDIN_MOUNTS=str(mounts))
    subprocess.run(['sh','install.sh','-y','-n','-t',str(dest)],cwd=folder,env=env,check=True,stdout=subprocess.DEVNULL)
    assert (dest/'piremote_addin.so').exists() and (dest/'install.sh').exists()
    text=unit.read_text();assert '/data/other-existing-addin.so' in text and str(dest/'piremote_addin.so') in text
    assert 'restart' not in log.read_text()
    subprocess.run(['sh','uninstall.sh','-y','-n','-t',str(dest)],cwd=dest,env=env,check=True,stdout=subprocess.DEVNULL)
    assert 'piremote_addin.so' not in unit.read_text() and '/data/other-existing-addin.so' in unit.read_text()
    assert not (dest/'piremote_addin.so').exists()
    print('PASS: packaged installer/uninstaller in fake systemd tree, other addin preserved, no real service touched')
