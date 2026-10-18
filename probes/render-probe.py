import ctypes as C
import time, json

egl=C.CDLL("libEGL.so.1"); gl=C.CDLL("libGLESv2.so.2")
def fn(lib,name,restype,args):
    f=getattr(lib,name); f.restype=restype; f.argtypes=args; return f
ptr=C.c_void_p; I=C.c_int; U=C.c_uint; F=C.c_float
getdisplay=fn(egl,"eglGetPlatformDisplay",ptr,[U,ptr,C.POINTER(I)])
initialize=fn(egl,"eglInitialize",U,[ptr,C.POINTER(I),C.POINTER(I)])
choose=fn(egl,"eglChooseConfig",U,[ptr,C.POINTER(I),C.POINTER(ptr),I,C.POINTER(I)])
bind=fn(egl,"eglBindAPI",U,[U])
surface=fn(egl,"eglCreatePbufferSurface",ptr,[ptr,ptr,C.POINTER(I)])
context=fn(egl,"eglCreateContext",ptr,[ptr,ptr,ptr,C.POINTER(I)])
make=fn(egl,"eglMakeCurrent",U,[ptr,ptr,ptr,ptr])
error=fn(egl,"eglGetError",U,[])
def check(v,label):
    if not v: raise RuntimeError(label+" EGL="+hex(error()))
print("START EGL initialization",flush=True)
d=getdisplay(0x31DD,None,None); check(d,"display")
a=I();b=I();check(initialize(d,C.byref(a),C.byref(b)),"initialize")
cfg=ptr();n=I()
attrs=(I*13)(0x3033,1,0x3040,4,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038)
check(choose(d,attrs,C.byref(cfg),1,C.byref(n)),"config");check(n.value,"config count")
check(bind(0x30A0),"bind")
s=surface(d,cfg,(I*5)(0x3057,512,0x3056,512,0x3038));check(s,"surface")
c=context(d,cfg,None,(I*3)(0x3098,2,0x3038));check(c,"context")
check(make(d,s,s,c),"make current")
string=fn(gl,"glGetString",C.c_char_p,[U])
renderer=string(0x1F01).decode();version=string(0x1F02).decode()
print(json.dumps(dict(renderer=renderer,version=version,egl=f"{a.value}.{b.value}")),flush=True)
from pathlib import Path
maps=Path('/proc/self/maps').read_text()
libs=sorted({line.split()[-1] for line in maps.splitlines() if '/opt/qy0z-mesa/' in line})
print(json.dumps(dict(custom_driver_libraries=libs)),flush=True)
import os
if os.environ.get('QY0Z_STOCK_NOCCS') == '1':
    assert 'qy0z' not in version, version
    assert os.environ.get('INTEL_DEBUG') == 'noccs'
    assert not libs, 'Custom libraries contaminated stock control'
    print(json.dumps(dict(control="stock Mesa with INTEL_DEBUG=noccs")),flush=True)
else:
    assert 'qy0z.1' in version, 'Custom Mesa version not active'
    assert any('gallium' in lib or 'iris_dri' in lib for lib in libs), 'Custom Iris library not mapped'

assert "intel" in renderer.lower() and not any(x in renderer.lower() for x in ("llvmpipe","softpipe")),renderer
clearcolor=fn(gl,"glClearColor",None,[F,F,F,F]);clear=fn(gl,"glClear",None,[U]);finish=fn(gl,"glFinish",None,[])
read=fn(gl,"glReadPixels",None,[I,I,I,I,U,U,ptr])
pixel=(C.c_ubyte*4)()
for color in [(1,0,0),(0,1,0),(0,0,1)]:
    clearcolor(*color,1);clear(0x4000);finish();read(256,256,1,1,0x1908,0x1401,pixel)
    assert all(abs(pixel[i]-color[i]*255)<=2 for i in range(3)),list(pixel)
print("PASS clear/readback RGB",flush=True)
create=fn(gl,"glCreateShader",U,[U]);source=fn(gl,"glShaderSource",None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)])
compile_=fn(gl,"glCompileShader",None,[U]);status=fn(gl,"glGetShaderiv",None,[U,U,C.POINTER(I)])
def shader(kind,src):
    sh=create(kind);p=C.c_char_p(src);source(sh,1,C.byref(p),None);compile_(sh);ok=I();status(sh,0x8B81,C.byref(ok));assert ok.value,"shader compilation";return sh
vs=shader(0x8B31,b"attribute vec2 p; void main(){gl_Position=vec4(p,0.,1.);}")
fs=shader(0x8B30,b"precision highp float; uniform float t; void main(){vec2 p=gl_FragCoord.xy/512.; float x=p.x+p.y+t; for(int i=0;i<24;i++){x=sin(x*1.17+0.1);} gl_FragColor=vec4(0.2+0.5*abs(x),0.4,0.7,1.);}")
program=fn(gl,"glCreateProgram",U,[])();attach=fn(gl,"glAttachShader",None,[U,U]);attach(program,vs);attach(program,fs)
fn(gl,"glBindAttribLocation",None,[U,U,C.c_char_p])(program,0,b"p")
fn(gl,"glLinkProgram",None,[U])(program)
ok=I();fn(gl,"glGetProgramiv",None,[U,U,C.POINTER(I)])(program,0x8B82,C.byref(ok));assert ok.value,"program link"
fn(gl,"glUseProgram",None,[U])(program)
vertices=(F*6)(-1,-1,3,-1,-1,3)
fn(gl,"glVertexAttribPointer",None,[U,I,U,U,I,ptr])(0,2,0x1406,0,0,C.cast(vertices,ptr))
fn(gl,"glEnableVertexAttribArray",None,[U])(0)
fn(gl,"glViewport",None,[I,I,I,I])(0,0,512,512)
loc=fn(gl,"glGetUniformLocation",I,[U,C.c_char_p])(program,b"t")
uniform=fn(gl,"glUniform1f",None,[I,F]);draw=fn(gl,"glDrawArrays",None,[U,I,I]);geterr=fn(gl,"glGetError",U,[])
start=time.monotonic();frames=0;last=start
while time.monotonic()-start<20:
    uniform(loc,(frames%100)/100);draw(4,0,3);finish();frames+=1
    if frames%30==0:
        read(256,256,1,1,0x1908,0x1401,pixel)
        assert abs(pixel[1]-102)<=2 and abs(pixel[2]-179)<=2,list(pixel)
        assert geterr()==0,"GL error"
    now=time.monotonic()
    if now-last>=5:
        print(json.dumps(dict(elapsed=round(now-start,2),frames=frames,pixel=list(pixel))),flush=True);last=now
    time.sleep(0.002)
print(json.dumps(dict(result="PASS",seconds=round(time.monotonic()-start,2),frames=frames,pixel=list(pixel))),flush=True)
fn(egl,"eglMakeCurrent",U,[ptr,ptr,ptr,ptr])(d,None,None,None)
fn(egl,"eglDestroyContext",U,[ptr,ptr])(d,c)
fn(egl,"eglDestroySurface",U,[ptr,ptr])(d,s)
fn(egl,"eglTerminate",U,[ptr])(d)
