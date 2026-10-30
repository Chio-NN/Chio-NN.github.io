import numpy as np
from scipy.io import wavfile
fs,y=wavfile.read('gibon_original_recortado.wav'); y=y/32768.0
t,f,_=np.load('analisis/f0_hilbert.npy')
def rdp(px,py,eps):
    def rec(i,j):
        if j<=i+1: return [i,j]
        x0,y0,x1,y1=px[i],py[i],px[j],py[j]
        yy=y0+(y1-y0)*(px[i+1:j]-x0)/(x1-x0); d=np.abs(py[i+1:j]-yy); k=np.argmax(d)
        if d[k]>eps: a=rec(i,i+1+k); b=rec(i+1+k,j); return a[:-1]+b
        return [i,j]
    return rec(0,len(px)-1)
# pitch in semitones re 830
tt=np.arange(0.03,1.275,0.005); ff=np.interp(tt,t,f)
k=5; ffs=np.convolve(ff,np.ones(k)/k,'same'); ffs[:3]=ff[:3]; ffs[-3:]=ff[-3:]
st=12*np.log2(ffs/830)
idx=rdp(tt,st,0.35)
print('PITCH bp:',[(round(tt[i],3),round(ffs[i])) for i in idx], len(idx))
# amplitude: RMS 40 ms
w=int(0.04*fs); rms=np.sqrt(np.convolve(y**2,np.ones(w)/w,'same')); ta=np.arange(len(y))/fs
ts=np.arange(0,1.302,0.005); a=20*np.log10(np.interp(ts,ta,rms)+1e-6)
idx=rdp(ts,a,2.0)
print('AMP bp:',[(round(ts[i],3),round(a[i],1)) for i in idx],len(idx))
np.save('analisis/contours.npy',{'tt':tt,'ff':ffs,'ts':ts,'a':a},allow_pickle=True)
