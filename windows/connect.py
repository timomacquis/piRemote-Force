"""Dedicated Pi Remote SSH connection. Never touches the Commander/Remote tunnels."""
from pathlib import Path
import subprocess,urllib.request,sys,json,ipaddress,time,datetime
PORT=16732
cache=Path.home()/'.cache/piremote';cache.mkdir(parents=True,exist_ok=True,mode=0o700)
control=cache/'ssh.sock';statefile=cache/'connection.json';keyfile=cache/'known-hosts'
def stop():
    if statefile.exists():
        old=json.loads(statefile.read_text())
        host=str(ipaddress.IPv4Address(old['host']))
        subprocess.run(['ssh','-S',str(control),'-O','exit','root@'+host],capture_output=True,timeout=8)
        statefile.unlink(missing_ok=True)
    if control.exists():control.unlink()
cmd=sys.argv[1] if len(sys.argv)>1 else 'connect'
host=sys.argv[2] if len(sys.argv)>2 else None
if cmd not in ('connect','disconnect','activate'):
    host=cmd;cmd='connect' # historical command line
if cmd=='disconnect':
    stop();print(json.dumps({'connected':False,'port':PORT}));sys.exit(0)
if host is None:raise SystemExit('Pass the Force IPv4 address.')
host=str(ipaddress.IPv4Address(host))
if statefile.exists():
    old=json.loads(statefile.read_text())
    alive=subprocess.run(['ssh','-S',str(control),'-O','check','root@'+str(ipaddress.IPv4Address(old['host']))],capture_output=True,timeout=5).returncode==0
    if old['host']==host and alive:
        try:
            info=json.loads(urllib.request.urlopen('http://127.0.0.1:'+str(PORT)+'/info',timeout=3).read())
            assert info.get('product')=='piremote','Unexpected service'
            print(json.dumps({'connected':True,'host':host,'port':PORT,'piremote':info}));sys.exit(0)
        except Exception:pass
    stop()
scan=subprocess.check_output(['ssh-keyscan','-T','5',host],stderr=subprocess.DEVNULL,timeout=12).decode()
known=Path.home().joinpath('.ssh/known_hosts').read_text()
keys={tuple(l.split()[1:3]) for l in known.splitlines() if len(l.split())>=3}
trusted=[l for l in scan.splitlines() if len(l.split())>=3 and tuple(l.split()[1:3]) in keys]
assert trusted,'Unknown SSH key: verify the Force identity'
keyfile.write_text('\n'.join(trusted)+'\n')
opts=['-o','BatchMode=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(keyfile)]
r=subprocess.run(['ssh']+opts+['root@'+host,'wget -q -T 3 -O - http://127.0.0.1:6732/info'],capture_output=True,timeout=12)
if r.returncode:
    installed=subprocess.run(['ssh']+opts+['root@'+host,'test -f /data/mpc-addins/piremote/install.sh'],capture_output=True,timeout=12)
    if installed.returncode==255:raise SystemExit('The Force could not be reached over SSH.')
    if installed.returncode:raise SystemExit('PIREMOTE_NOT_INSTALLED: install the Force ZIP first.')
    if cmd!='activate':raise SystemExit('ACTIVATION_REQUIRED: piRemote is installed but inactive.')
    if '--project-saved' not in sys.argv:raise SystemExit('Activation requires explicit confirmation that the project is saved.')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')
    before=subprocess.check_output(['ssh']+opts+['root@'+host,'systemctl cat acvs'],timeout=12)
    (cache/('service-before-'+stamp+'.txt')).write_bytes(before)
    subprocess.run(['ssh']+opts+['root@'+host,'sh /data/mpc-addins/piremote/install.sh -y -n -t /data/mpc-addins/piremote && systemctl restart acvs'],check=True,timeout=45)
    for _ in range(12):
        time.sleep(1)
        r=subprocess.run(['ssh']+opts+['root@'+host,'wget -q -T 2 -O - http://127.0.0.1:6732/info'],capture_output=True,timeout=10)
        if r.returncode==0:break
    else:raise SystemExit('Activation did not start piRemote. Use the recovery steps in INSTALL.md.')
info=json.loads(r.stdout)
if info.get('product')!='piremote':raise SystemExit('Unexpected service at the piRemote port.')
subprocess.run(['ssh','-M','-S',str(control),'-f','-N']+opts+['-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-L','127.0.0.1:'+str(PORT)+':127.0.0.1:6732','root@'+host],check=True,timeout=15)
statefile.write_text(json.dumps({'host':host,'port':PORT}))
print(json.dumps({'connected':True,'host':host,'port':PORT,'piremote':info}))
