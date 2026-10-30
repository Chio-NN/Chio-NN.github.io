import numpy as np
from scipy.signal import lfilter
def lufs(y,fs=48000):
    # ITU-R BS.1770-4: filtro K (dos biquads para 48 kHz) + compuerta absoluta y relativa
    b1=[1.53512485958697,-2.69169618940638,1.19839281085285]; a1=[1,-1.69065929318241,0.73248077421585]
    b2=[1.0,-2.0,1.0]; a2=[1,-1.99004745483398,0.99007225036621]
    z=lfilter(b2,a2,lfilter(b1,a1,y)); B=int(0.4*fs); H=int(0.1*fs)
    ms=np.array([np.mean(z[i:i+B]**2) for i in range(0,len(z)-B+1,H)])
    l=-0.691+10*np.log10(ms+1e-20); g=ms[l>-70]
    rel=-0.691+10*np.log10(g.mean())-10; g2=ms[(l>-70)&(l>rel)]
    return -0.691+10*np.log10(g2.mean())
