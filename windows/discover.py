"""Read-only MPC discovery using existing WSL SSH trust and keys. No activation or tunnel changes."""
from pathlib import Path
import concurrent.futures,ipaddress,json,subprocess,sys,tempfile

def host_keys(text):
 return {tuple(line.split()[1:3]) for line in text.splitlines() if len(line.split())>=3 and not line.startswith(('#','@revoked','@cert-authority'))}

def probe(host,known,run=subprocess.run):
 host=str(ipaddress.IPv4Address(host))
 try:
  scan=run(['ssh-keyscan','-T','2',host],capture_output=True,text=True,timeout=4).stdout
  trusted=[line for line in scan.splitlines() if len(line.split())>=3 and tuple(line.split()[1:3]) in known]
  if not trusted:return None
  with tempfile.TemporaryDirectory(prefix='piremote-find-') as folder:
   keyfile=Path(folder)/'known_hosts';keyfile.write_text('\n'.join(trusted)+'\n')
   cmd=['ssh','-o','BatchMode=yes','-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','-o','ConnectTimeout=2','-o','ConnectionAttempts=1','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(keyfile),'root@'+host,'test -x /usr/bin/MPC && hostname']
   result=run(cmd,capture_output=True,text=True,timeout=5)
   if result.returncode==0:return {'host':host,'name':result.stdout.strip()[:100]}
 except (OSError,subprocess.TimeoutExpired):pass
 return None

def discover(hosts,known):
 addresses=sorted({str(ipaddress.IPv4Address(h)) for h in hosts},key=ipaddress.IPv4Address)
 if len(addresses)>128:raise ValueError('Too many SSH candidates')
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  return [r for r in pool.map(lambda h:probe(h,known),addresses) if r]

if __name__=='__main__':
 known_file=Path.home()/'.ssh/known_hosts'
 if not known_file.exists():raise SystemExit('No trusted SSH hosts. Connect from WSL and verify the device fingerprint first.')
 hosts=sys.argv[1].split(',') if len(sys.argv)>1 and sys.argv[1] else []
 print(json.dumps({'devices':discover(hosts,host_keys(known_file.read_text()))}))
