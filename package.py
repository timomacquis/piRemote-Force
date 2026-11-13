"""Assemble standalone Force / Windows / source ZIPs. No device or network access."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,re,sys
B=Path(__file__).resolve().parent;V='0.1.0';D=B/'dist'/V;D.mkdir(parents=True,exist_ok=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
force=json.loads((B/'build/BUILD.json').read_text());windows=json.loads((B/'build/windows/BUILD.json').read_text(encoding='utf-8-sig'))
assert sha((B/'build/piremote_addin.so').read_bytes())==force['output_sha256']
for name,digest in force['inputs'].items():assert sha((B/name).read_bytes())==digest,name
assert sha((B/'build/windows/πRemote.exe').read_bytes())==windows['exe_sha256']
for name,digest in windows['inputs'].items():assert sha((B/'windows'/name).read_bytes())==digest,name
commit=None
if (B/'.git').exists():commit=subprocess.check_output(['git','-C',str(B),'rev-parse','HEAD'],text=True).strip()
provenance={'version':V,'source_repo':'https://github.com/timomacquis/piRemote-Force','source_commit':commit,'force':force,'windows':windows,'installer_commit':(B/'packaging/UPSTREAM-COMMIT.txt').read_text().strip(),'tests':'Offline ASan/UBSan + fake MPC HTTP + native Windows connection lifecycle; device pending'}
prov=(json.dumps(provenance,indent=2)+'\n').encode()
common={n:(B/n).read_bytes() for n in ['LICENSE','THIRD-PARTY.md']}
fm={**common,'piremote_addin.so':(B/'build/piremote_addin.so').read_bytes(),'INSTALL.md':(B/'INSTALL.md').read_bytes(),'USAGE.md':(B/'INSTALL.md').read_bytes(),'PROVENANCE.json':prov}
for n in ['install.sh','uninstall.sh','addin-lib.sh','addin.manifest','piremote.conf']:fm[n]=(B/'packaging'/n).read_bytes()
files=['LICENSE','THIRD-PARTY.md','PROVENANCE.json','USAGE.md']
manifest={'schema':1,'id':'piremote','name':'πRemote','version':V,'kind':'addin','layout':'addin','so':'piremote_addin.so','conf':'piremote.conf','files':files,'user_data':['piremote.conf'],'arch':'armv7','max_glibc':max(force['glibc_versions'],key=lambda v:tuple(map(int,v.split('.')))),'param_compat':0,'about':'Independent transport and physical-button navigation companion for the official Remote Screen. Localhost only; use the Windows app over SSH. Offline-tested preview.','requires':'Force Gen1 OS 3.10.1; official SSH access; Windows companion','source_repo':'timomacquis/piRemote-Force','license':'MIT','cpu':None}
fm['mpc-plugin.json']=(json.dumps(manifest,indent=2)+'\n').encode()
wm={**common,'README.md':(B/'windows/README.md').read_bytes(),'PROVENANCE.json':prov,'Force-IP.txt':b''}
for n in ['πRemote.exe','πRemote.exe.config','piRemote.ico','connect.py','Activate-Force.ps1']:wm[n]=(B/'build/windows'/n).read_bytes()
sm={}
tracked=None
if (B/'.git').exists():tracked=set(subprocess.check_output(['git','-C',str(B),'ls-files','-z']).decode().split('\0'))
for p in B.rglob('*'):
    rel=p.relative_to(B)
    if not p.is_file() or rel.parts[0] in ['build','dist','.git'] or '__pycache__' in rel.parts or p.suffix=='.pyc' or p.name=='Force-IP.txt':continue
    if tracked is not None and rel.as_posix() not in tracked:continue
    sm[str(rel).replace('\\','/')]=p.read_bytes()
outputs=[]
for kind,contents in [('mpc-armv7',fm),('windows',wm),('source',sm)]:
    if kind=='mpc-armv7' and '--keep-force' in sys.argv:
        path=D/f'piRemote-{V}-mpc-armv7.zip';assert path.exists()
        digest=sha(path.read_bytes());assert path.with_suffix(path.suffix+'.sha256').read_text().split()[0]==digest
        outputs.append({'file':path.name,'sha256':digest,'bytes':path.stat().st_size});print('Unchanged Force ZIP:',path.name,digest);continue
    contents=dict(contents);contents['SHA256SUMS']=''.join(sha(raw)+'  '+name+'\n' for name,raw in sorted(contents.items())).encode()
    name=f'piRemote-{V}-{kind}.zip';top=f'piRemote-{V}-{kind}';path=D/name
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,raw in sorted(contents.items()):
            info=zipfile.ZipInfo(top+'/'+n,(2026,11,13,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED
            executable=n.endswith('.sh') or n.endswith('.so');info.external_attr=(0o100755 if executable else 0o100644)<<16
            z.writestr(info,raw)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for line in z.read(top+'/SHA256SUMS').decode().splitlines():
            digest,n=line.split('  ',1);assert sha(z.read(top+'/'+n))==digest
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    digest=sha(path.read_bytes());path.with_suffix(path.suffix+'.sha256').write_text(digest+'  '+name+'\n')
    outputs.append({'file':name,'sha256':digest,'bytes':path.stat().st_size});print(name,path.stat().st_size,'bytes',digest)
(D/'PACKAGES.json').write_text(json.dumps({'version':V,'device_tested':False,'packages':outputs},indent=2)+'\n')
