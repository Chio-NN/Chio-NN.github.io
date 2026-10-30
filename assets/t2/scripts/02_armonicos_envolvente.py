import numpy as np
from scipy.io import wavfile
from scipy.signal import find_peaks
fs,x=wavfile.read('gibon_original.wav'); x=x/32768.0; y=x[:int(1.302*fs)]
t0,f0,_=np.load('analisis/f0.npy')
# harmonic tracks, hop 10ms, win 40ms
L=int(0.04*fs); hop=int(0.01*fs); NF=16384
F=np.fft.rfftfreq(NF,1/fs)
T=[];H=[];Nz=[]
for a in range(0,len(y)-L,hop):
    s=y[a:a+L]; w=np.hanning(L); S=np.abs(np.fft.rfft(s*w,NF))*2/w.sum()
    tc=(a+L/2)/fs; fz=np.interp(tc,t0,f0)
    row=[]
    mask=np.ones_like(F,bool)
    for h in range(1,13):
        m=(F>h*fz-fz*0.15)&(F<h*fz+fz*0.15); row.append(20*np.log10(S[m].max()+1e-12)); mask&=~((F>h*fz-fz*0.25)&(F<h*fz+fz*0.25))
    nb=mask&(F>1500)&(F<12000)
    Nz.append(10*np.log10(np.mean(S[nb]**2)+1e-20))
    T.append(tc);H.append(row)
T=np.array(T);H=np.array(H);Nz=np.array(Nz)
np.save('analisis/harm.npy',np.column_stack([T,H,Nz]))
for i in range(0,len(T),5):
    print(f'{T[i]:.2f} '+' '.join(f'{v:4.0f}' for v in H[i])+f' | noise {Nz[i]:.0f}')
# envelope
w=int(0.01*fs); rms=np.sqrt(np.convolve(y**2,np.ones(w)/w,'same'))
tt=np.arange(len(y))/fs
e=rms[::int(0.001*fs)]; te=tt[::int(0.001*fs)]
edb=20*np.log10(e+1e-9)
pk,_=find_peaks(edb,prominence=3,distance=15)
print('env peaks (t, dB):',[(round(te[p],3),round(edb[p],1)) for p in pk])
print('max env',te[np.argmax(edb)],edb.max())
np.save('analisis/env.npy',np.vstack([te,e]))
