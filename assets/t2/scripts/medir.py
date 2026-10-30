import numpy as np, sys
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert
def cargar(p, dur=1.302):
    fs,y=wavfile.read(p); y=y.astype(float)/32768.0
    if y.ndim>1: y=y[:,0]
    return fs,y[:int(dur*fs)]
def niveles(fs,y,t0f,f0f):
    L=int(0.04*fs); hop=int(0.01*fs); NF=16384; F=np.fft.rfftfreq(NF,1/fs); T=[];H=[];Nz=[]
    for a in range(0,len(y)-L,hop):
        s=y[a:a+L]; w=np.hanning(L); S=np.abs(np.fft.rfft(s*w,NF))*2/w.sum()
        tc=(a+L/2)/fs; fz=np.interp(tc,t0f,f0f); row=[]; mask=np.ones_like(F,bool)
        for h in range(1,13):
            m=(F>h*fz-fz*0.15)&(F<h*fz+fz*0.15); row.append(20*np.log10(S[m].max()+1e-12)); mask&=~((F>h*fz-fz*0.25)&(F<h*fz+fz*0.25))
        nb=mask&(F>1500)&(F<12000); Nz.append(10*np.log10(np.mean(S[nb]**2)+1e-20)); T.append(tc); H.append(row)
    return np.array(T),np.array(H),np.array(Nz)
def f0track(fs,y):
    sos=butter(10,1130,'low',fs=fs,output='sos'); a=hilbert(sosfiltfilt(sos,y))
    inst=np.diff(np.unwrap(np.angle(a)))*fs/(2*np.pi); k=int(0.01*fs); inst=np.convolve(inst,np.ones(k)/k,'same')
    t=np.arange(len(inst))/fs; return t,inst
def resumen(p):
    fs,y=cargar(p); t,f=f0track(fs,y); T,H,Nz=niveles(fs,y,t,f)
    rel=H-H[:,[0]]
    out={}
    for nombre,(a,b) in {'pico 0,15-0,40':(0.15,0.40),'meseta 0,55-0,80':(0.55,0.80),'final 1,12-1,25':(1.12,1.25)}.items():
        m=(T>a)&(T<b)
        out[nombre]=dict(h2=np.median(rel[m,1]), h3_8=np.median(10*np.log10(np.mean(10**(rel[m,2:8]/10),axis=1))), ruido=np.median(Nz[m]-H[m,0]))
    return out,(t,f),(T,H,Nz)
if __name__=='__main__':
    for p in sys.argv[1:]:
        o,(t,f),_=resumen(p); print(p)
        for k,v in o.items(): print(f'   {k:18s} H2 {v["h2"]:6.1f}  H3-8 {v["h3_8"]:6.1f}  ruido {v["ruido"]:6.1f}')
        print('   f0 @0.25/0.7/1.2:', [round(float(np.interp(x,t,f))) for x in (0.25,0.7,1.2)])
