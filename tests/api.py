from pathlib import Path
import subprocess,tempfile,os,time,json,urllib.request,urllib.error,socket
B=Path(__file__).resolve().parents[1];O=B/'build/native'
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp);capture=tmp/'capture.bin';conf=tmp/'piremote.conf'
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    conf.write_text(f'enabled=1\nbind=127.0.0.1\nport={port}\n')
    env=dict(os.environ,PIREMOTE_ADDIN_CONF=str(conf),TEST_CAPTURE=str(capture),ASAN_OPTIONS='detect_leaks=0:abort_on_error=1')
    with (tmp/'stderr').open('wb') as errors:
        p=subprocess.Popen([str(O/'MPC')],env=env,stderr=errors)
        try:
            base=f'http://127.0.0.1:{port}'
            for _ in range(100):
                if p.poll() is not None:raise RuntimeError((tmp/'stderr').read_text())
                try:
                    info=json.load(urllib.request.urlopen(base+'/info',timeout=.3))
                    if info['ready']:break
                except OSError:time.sleep(.05)
            else:raise RuntimeError('server did not start')
            assert info['product']=='piremote'
            def post(obj):
                req=urllib.request.Request(base+'/command',data=json.dumps(obj).encode(),headers={'Content-Type':'application/json'})
                return json.load(urllib.request.urlopen(req,timeout=2))
            assert post({'t':'transport','cmd':'play'})['ok'];time.sleep(.2)
            state=json.load(urllib.request.urlopen(base+'/state'));assert state['playing'] and state['source']=='buttons' and not state['authoritative']
            assert post({'t':'transport','cmd':'stop'})['ok'];time.sleep(.2)
            assert not json.load(urllib.request.urlopen(base+'/state'))['playing']
            assert post({'t':'surface','bytes':[144,37,127,144,96,127,144,96,0,144,37,0]})['ok']
            assert post({'t':'surface','bytes':[144,49,127]})['ok'];time.sleep(1.4)
            raw=capture.read_bytes();assert bytes([144,82,127]) in raw and bytes([144,82,0]) in raw
            assert bytes([144,49,0]) in raw
            before=len(raw)
            try:post({'t':'surface','bytes':[153,36,127]});raise AssertionError('pad accepted')
            except urllib.error.HTTPError as e:assert e.code==400
            assert post({'t':'release'})['ok'];time.sleep(.2);assert len(capture.read_bytes())==before
            with socket.create_connection(('127.0.0.1',port)) as s:
                s.sendall(b'GET /info HTTP/1.1\r\nHost: evil.example\r\n\r\n');assert b'400' in s.recv(1024)
            assert p.poll() is None
            print('PASS: real HTTP addin + fake MPC reads, transport/navigation, watchdog, rejected pads, no hardware')
        finally:p.terminate();p.wait(timeout=5)
    errors=(tmp/'stderr').read_text();assert 'ERROR: AddressSanitizer' not in errors and 'runtime error:' not in errors,errors
