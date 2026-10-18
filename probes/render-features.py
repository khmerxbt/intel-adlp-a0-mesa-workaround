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

# Exercise paths used by 3D emulators beyond simple color clears.
genfb=fn(gl,"glGenFramebuffers",None,[I,C.POINTER(U)])
bindfb=fn(gl,"glBindFramebuffer",None,[U,U])
genrb=fn(gl,"glGenRenderbuffers",None,[I,C.POINTER(U)])
bindrb=fn(gl,"glBindRenderbuffer",None,[U,U])
store=fn(gl,"glRenderbufferStorage",None,[U,U,I,I])
storems=fn(gl,"glRenderbufferStorageMultisample",None,[U,I,U,I,I])
attachrb=fn(gl,"glFramebufferRenderbuffer",None,[U,U,U,U])
statusfb=fn(gl,"glCheckFramebufferStatus",U,[U])
blit=fn(gl,"glBlitFramebuffer",None,[I,I,I,I,I,I,I,I,U,U])
enable=fn(gl,"glEnable",None,[U]);disable=fn(gl,"glDisable",None,[U])
viewport=fn(gl,"glViewport",None,[I,I,I,I])
getinteger=fn(gl,"glGetIntegerv",None,[U,C.POINTER(I)])
getloc=fn(gl,"glGetUniformLocation",I,[U,C.c_char_p])
use=fn(gl,"glUseProgram",None,[U]);u1=fn(gl,"glUniform1f",None,[I,F])
u4=fn(gl,"glUniform4f",None,[I,F,F,F,F])

def make_program(vsrc,fsrc):
    p=fn(gl,"glCreateProgram",U,[])()
    attach(p,shader(0x8B31,vsrc));attach(p,shader(0x8B30,fsrc))
    fn(gl,"glBindAttribLocation",None,[U,U,C.c_char_p])(p,0,b"p")
    fn(gl,"glLinkProgram",None,[U])(p)
    ok=I();fn(gl,"glGetProgramiv",None,[U,U,C.POINTER(I)])(p,0x8B82,C.byref(ok));assert ok.value
    return p

prog=make_program(b"attribute vec2 p; uniform float z; void main(){gl_Position=vec4(p,z,1.);}",
                  b"precision highp float; uniform vec4 rgba; void main(){gl_FragColor=rgba;}")
use(prog);zloc=getloc(prog,b"z");cloc=getloc(prog,b"rgba")

def framebuffer(samples,depth=True):
    fb=U();genfb(1,C.byref(fb));bindfb(0x8D40,fb.value)
    rb=U();genrb(1,C.byref(rb));bindrb(0x8D41,rb.value)
    if samples>1:storems(0x8D41,samples,0x8058,64,64)
    else:store(0x8D41,0x8058,64,64)
    attachrb(0x8D40,0x8CE0,0x8D41,rb.value)
    if depth:
        ds=U();genrb(1,C.byref(ds));bindrb(0x8D41,ds.value)
        if samples>1:storems(0x8D41,samples,0x88F0,64,64)
        else:store(0x8D41,0x88F0,64,64)
        attachrb(0x8D40,0x821A,0x8D41,ds.value)
    assert statusfb(0x8D40)==0x8CD5,hex(statusfb(0x8D40))
    return fb.value

def check_pixel(expected,label):
    finish();read(32,32,1,1,0x1908,0x1401,pixel)
    assert all(abs(pixel[i]-expected[i])<=2 for i in range(4)),(label,list(pixel))
    assert geterr()==0,label
    print(json.dumps(dict(test=label,pixel=list(pixel),result="PASS")),flush=True)

def draw_color(z,rgba):
    u1(zloc,z);u4(cloc,*rgba);draw(4,0,3)

resolved=framebuffer(1,False)
maxsamples=I();getinteger(0x8D57,C.byref(maxsamples));assert maxsamples.value>=4,maxsamples.value
stencilfunc=fn(gl,"glStencilFunc",None,[U,I,U]);stencilop=fn(gl,"glStencilOp",None,[U,U,U])
for samples in [1,4]:
    fb=framebuffer(samples)
    viewport(0,0,64,64);use(prog)
    disable(0x0B71);disable(0x0B90)
    clearcolor(0,0,0,1);fn(gl,"glClearDepthf",None,[F])(1)
    fn(gl,"glClearStencil",None,[I])(0);clear(0x4000|0x0100|0x0400)
    enable(0x0B71);fn(gl,"glDepthFunc",None,[U])(0x0201)
    enable(0x0B90);stencilfunc(0x0207,1,255);stencilop(0x1E00,0x1E00,0x1E01)
    draw_color(0,(1,0,0,1))
    stencilop(0x1E00,0x1E00,0x1E00)
    draw_color(.5,(0,1,0,1))
    if samples>1:
        bindfb(0x8CA8,fb);bindfb(0x8CA9,resolved)
        blit(0,0,64,64,0,0,64,64,0x4000,0x2600);bindfb(0x8CA8,resolved)
    check_pixel([255,0,0,255],f"depth-occlusion-{samples}x")
    bindfb(0x8D40,fb);disable(0x0B71)
    stencilfunc(0x0202,0,255);draw_color(0,(0,1,0,1))
    if samples>1:
        bindfb(0x8CA8,fb);bindfb(0x8CA9,resolved)
        blit(0,0,64,64,0,0,64,64,0x4000,0x2600);bindfb(0x8CA8,resolved)
    check_pixel([255,0,0,255],f"stencil-rejection-{samples}x")
    bindfb(0x8D40,fb);stencilfunc(0x0202,1,255);draw_color(0,(0,1,0,1))
    if samples>1:
        bindfb(0x8CA8,fb);bindfb(0x8CA9,resolved)
        blit(0,0,64,64,0,0,64,64,0x4000,0x2600);bindfb(0x8CA8,resolved)
    check_pixel([0,255,0,255],f"stencil-acceptance-{samples}x")
    disable(0x0B90)

bindfb(0x8D40,resolved)
tex=U();fn(gl,"glGenTextures",None,[I,C.POINTER(U)])(1,C.byref(tex))
fn(gl,"glBindTexture",None,[U,U])(0x0DE1,tex.value)
fn(gl,"glTexParameteri",None,[U,U,I])(0x0DE1,0x2801,0x2600)
fn(gl,"glTexParameteri",None,[U,U,I])(0x0DE1,0x2800,0x2600)
fn(gl,"glCopyTexImage2D",None,[U,I,U,I,I,I,I,I])(0x0DE1,0,0x1908,0,0,64,64,0)
textureprog=make_program(b"attribute vec2 p; void main(){gl_Position=vec4(p,0.,1.);}",
    b"precision highp float; uniform sampler2D tex; void main(){gl_FragColor=texture2D(tex,gl_FragCoord.xy/64.);}")
dest=framebuffer(1,False);viewport(0,0,64,64)
clearcolor(1,0,0,1);clear(0x4000);use(textureprog)
fn(gl,"glUniform1i",None,[I,I])(getloc(textureprog,b"tex"),0)
draw(4,0,3);check_pixel([0,255,0,255],"texture-copy-and-sample")
print(json.dumps(dict(result="PASS",features=["depth","stencil","4xMSAA-resolve","texture-copy-and-sampling"])),flush=True)
fn(egl,"eglMakeCurrent",U,[ptr,ptr,ptr,ptr])(d,None,None,None)
fn(egl,"eglDestroyContext",U,[ptr,ptr])(d,c)
fn(egl,"eglDestroySurface",U,[ptr,ptr])(d,s)
fn(egl,"eglTerminate",U,[ptr])(d)
