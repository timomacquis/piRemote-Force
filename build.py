"""Build and test offline. Never connects to a device."""
from pathlib import Path
import subprocess,os,re,json,hashlib
B=Path(__file__).resolve().parent;N=B/'build/native';N.mkdir(parents=True,exist_ok=True)
def run(args,**kw):subprocess.run(list(map(str,args)),check=True,**kw)
flags=['-std=c11','-Wall','-Wextra','-Werror','-fno-common'];san=['-fsanitize=address,undefined','-g']
src=B/'src';vendor=src/'vendor'
run(['gcc',*flags,*san,'-I'+str(src),B/'tests/unit.c',src/'control.c',src/'http.c',vendor/'json.c','-o',N/'unit'])
run([N/'unit'])
run(['gcc',*flags,*san,'-shared','-fPIC',vendor/'fake_asound.c','-o',N/'libfake_asound.so'])
run(['gcc',*flags,*san,'-shared','-fPIC','-fvisibility=hidden',src/'addin.c',src/'control.c',src/'http.c',vendor/'json.c',vendor/'surface.c','-lpthread','-ldl','-o',N/'libpiremote.so'])
run(['gcc',*flags,*san,B/'tests/fake_mpc.c','-L'+str(N),'-Wl,--no-as-needed','-lpiremote','-lfake_asound','-lpthread','-Wl,-rpath,'+str(N),'-o',N/'MPC'])
run(['python3',B/'tests/api.py'])
# Upstream stream-boundary and running-status tests are kept unchanged except for their include path.
run(['gcc',*flags,*san,'-shared','-fPIC',vendor/'surface.c','-lpthread','-ldl','-o',N/'libsurface.so'])
(N/'surface_test.c').write_text((vendor/'surface_test.c').read_text().replace('#include "../src/surface.h"','#include "surface.h"'))
run(['gcc',*flags,*san,'-I'+str(vendor),N/'surface_test.c','-L'+str(N),'-Wl,--no-as-needed','-lsurface','-lfake_asound','-lpthread','-ldl','-Wl,-rpath,'+str(N),'-o',N/'surface_test'])
run([N/'surface_test'])
root=Path(os.environ.get('PIREMOTE_TOOLCHAIN_ROOT',str(B.parent/'πClideaN/toolchain/root')));usr=root/'usr'
env=dict(os.environ,PATH=str(usr/'bin')+':'+os.environ['PATH'],LD_LIBRARY_PATH=str(usr/'lib/x86_64-linux-gnu')+':'+os.environ.get('LD_LIBRARY_PATH',''))
out=B/'build/piremote_addin.so'
run([usr/'bin/arm-linux-gnueabihf-gcc-12','--sysroot='+str(root),*flags,'-O2','-fPIC','-shared','-fvisibility=hidden','-march=armv7-a','-mfpu=neon','-mfloat-abi=hard',src/'addin.c',src/'control.c',src/'http.c',vendor/'json.c',vendor/'surface.c','-lpthread','-ldl','-Wl,-z,relro,-z,now,-z,noexecstack','-o',out],env=env)
run([usr/'bin/arm-linux-gnueabihf-strip',out],env=env)
elf=subprocess.check_output([str(usr/'bin/arm-linux-gnueabihf-readelf'),'-h','-d','--version-info','-Ws',str(out)],env=env,text=True)
(B/'build/ELF.txt').write_text(elf)
assert 'ARM' in elf and 'ELF32' in elf
versions=set(re.findall(r'GLIBC_([0-9.]+)',elf));assert all(tuple(map(int,v.split('.')))<=(2,39) for v in versions),versions
report={'version':'0.1.0','architecture':'ARMv7 hard-float','target':'Force Gen1 OS 3.10.1; no device validation yet','output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'glibc_versions':sorted(versions),'surface_commit':(vendor/'COMMIT.txt').read_text().strip(),'json_commit':(vendor/'JSON-COMMIT.txt').read_text().strip(),'inputs':{str(p.relative_to(B)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(src.rglob('*')) if p.is_file()},'offline_tests':['ASan/UBSan unit','ASan/UBSan fake MPC HTTP integration','ASan/UBSan upstream surface'],'installed':False}
(B/'build/BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print('ARM32 addin built:',out.stat().st_size,'bytes; SHA256',report['output_sha256'])
