"""Discovery trust, command bounds and read-only behavior without network access."""
from pathlib import Path
import importlib.util,subprocess
B=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('discover',B/'windows/discover.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
key='ssh-ed25519 AAAA_TEST_KEY';known=m.host_keys('old-host '+key+'\n@revoked bad ssh-ed25519 REVOKED\n#comment\n')
assert known=={('ssh-ed25519','AAAA_TEST_KEY')}
commands=[]
def run(args,**kw):
 commands.append(args)
 if args[0]=='ssh-keyscan':return subprocess.CompletedProcess(args,0,'10.0.0.70 '+key+'\n','')
 assert args[-1]=='test -x /usr/bin/MPC && hostname'
 assert 'StrictHostKeyChecking=yes' in args and 'PasswordAuthentication=no' in args
 assert 'root@10.0.0.70' in args
 return subprocess.CompletedProcess(args,0,'Force\n','')
assert m.probe('10.0.0.70',known,run)=={'host':'10.0.0.70','name':'Force'}
commands.clear();assert m.probe('10.0.0.70',set(),run) is None and len(commands)==1
def timeout(*a,**kw):raise subprocess.TimeoutExpired(a[0],1)
assert m.probe('10.0.0.70',known,timeout) is None
try:m.probe('1.2.3.4; restart',known,run);raise AssertionError('invalid address accepted')
except ValueError:pass
try:m.discover(['10.0.0.'+str(i) for i in range(1,130)],known);raise AssertionError('unbounded SSH probes')
except ValueError:pass
print('PASS: trusted changed-IP discovery, unknown-key rejection, no password or mutation commands, timeout and address/candidate bounds')
