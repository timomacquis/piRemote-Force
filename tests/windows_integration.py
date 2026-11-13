"""Real Windows executable against the sanitized addin + fake hardware in WSL. No SSH/device."""
from pathlib import Path
import os,subprocess,tempfile,socket,time,json
B=Path(__file__).resolve().parents[1];N=B/'build/native';out=B/'build/windows/CONNECTION-TEST.json'
exe=B/'build/windows/πRemote.exe'
assert exe.exists(),'Build windows/Build-App.ps1 first'
def windows(path):
    text=str(path);assert text.startswith('/mnt/c/');return 'C:\\'+text[7:].replace('/','\\')
with tempfile.TemporaryDirectory() as temp:
    temp=Path(temp);capture=temp/'capture.bin';conf=temp/'piremote.conf'
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    conf.write_text(f'enabled=1\nbind=127.0.0.1\nport={port}\n')
    env=dict(os.environ,PIREMOTE_ADDIN_CONF=str(conf),TEST_CAPTURE=str(capture),ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
    with (temp/'stderr').open('wb') as stderr:
        p=subprocess.Popen([str(N/'MPC')],env=env,stderr=stderr)
        try:
            for _ in range(100):
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=.1):break
                except OSError:time.sleep(.05)
            else:raise RuntimeError('fake MPC server not listening')
            command="$p=Start-Process -FilePath '"+windows(exe)+"' -ArgumentList @('--connection-test','\""+windows(out)+"\"','http://127.0.0.1:"+str(port)+"') -Wait -PassThru; exit $p.ExitCode"
            subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-Command',command],check=True,timeout=60)
            result=json.loads(out.read_text(encoding='utf-8-sig'));assert result['connected'] and result['disconnected'] and result['reconnected'],result
            assert capture.read_bytes()==b'', 'Windows connection test emitted a physical command'
            print('PASS: native Windows UI connects, disconnects and reconnects to independent addin; zero physical commands')
        finally:p.terminate();p.wait(timeout=5)
    errors=(temp/'stderr').read_text();assert 'ERROR: AddressSanitizer' not in errors and 'runtime error:' not in errors,errors
