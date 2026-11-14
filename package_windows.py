"""Package the Windows-only 0.1.1 update; leave every Force asset unchanged."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
B=Path(__file__).resolve().parent;V='0.1.1';D=B/'dist'/V;D.mkdir(parents=True,exist_ok=True)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
r=json.loads((B/'build/windows/BUILD.json').read_text(encoding='utf-8-sig'));assert r['version']==V
assert sha((B/'build/windows/πRemote.exe').read_bytes())==r['exe_sha256']
for n,h in r['inputs'].items():assert sha((B/'windows'/n).read_bytes())==h,n
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=B,text=True).strip()
files={n:(B/'build/windows'/n).read_bytes() for n in ['πRemote.exe','πRemote.exe.config','piRemote.ico','connect.py','discover.py','Activate-Force.ps1']}
files.update({'Force-IP.txt':b'','README.md':(B/'windows/README.md').read_bytes(),'LICENSE':(B/'LICENSE').read_bytes(),'THIRD-PARTY.md':(B/'THIRD-PARTY.md').read_bytes(),'PROVENANCE.json':(json.dumps(dict(windows_version=V,force_addin_version='0.1.0',source_commit=commit,build=r,user_validated_find='2026-11-14'),indent=2)+'\n').encode()})
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=B).decode().split('\0');source={n:(B/n).read_bytes() for n in tracked if n and (B/n).is_file() and not n.endswith('Force-IP.txt')}
for name,contents in [(f'piRemote-{V}-windows',files),(f'piRemote-{V}-source',source)]:
 contents=dict(contents);contents['SHA256SUMS']=''.join(sha(v)+'  '+k+'\n' for k,v in sorted(contents.items())).encode();path=D/(name+'.zip')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for n,v in sorted(contents.items()):z.writestr(name+'/'+n,v)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  for line in z.read(name+'/SHA256SUMS').decode().splitlines():
   digest,n=line.split('  ',1);assert sha(z.read(name+'/'+n))==digest
 Path(str(path)+'.sha256').write_text(sha(path.read_bytes())+'  '+path.name+'\n');print(path.name,sha(path.read_bytes()))
