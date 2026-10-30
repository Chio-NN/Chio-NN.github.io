import numpy as np, json
from scipy.io import wavfile
from scipy.signal import stft, butter, sosfiltfilt, find_peaks
fs,x=wavfile.read('gibon_original.wav'); x=x/32768.0
end=int(1.302*fs); y=x[:end]
print('dur',len(y)/fs,'peak dBFS',20*np.log10(np.abs(y).max()))
# HF content check (compression cutoff)
Y=np.abs(np.fft.rfft(y*np.hanning(len(y)))); F=np.fft.rfftfreq(len(y),1/fs)
for lo,hi in [(0,4e3),(4e3,8e3),(8e3,12e3),(12e3,16e3),(16e3,20e3),(20e3,24e3)]:
    m=(F>=lo)&(F<hi); print(f'band {lo/1e3:.0f}-{hi/1e3:.0f} kHz: {10*np.log10(np.mean(Y[m]**2)):.1f} dB')
# f0 track
N=2048;hop=120
f,t,Z=stft(y,fs,window='hann',nperseg=N,noverlap=N-hop,boundary='zeros',padded=True)
M=np.abs(Z)*2/np.hanning(N).sum()
band=(f>300)&(f<1600); i0=np.argmax(band)
f0=[];a0=[]
for j in range(M.shape[1]):
    col=M[:,j]; k=np.argmax(col[band])+i0
    a,b,c=np.log(col[k-1:k+2]+1e-15); p=0.5*(a-c)/(a-2*b+c)
    f0.append((k+p)*fs/N); a0.append(20*np.log10(np.exp(b-0.25*(a-c)*p)))
f0=np.array(f0);a0=np.array(a0)
ok=(t>0.02)&(t<1.28)
for tt in np.arange(0.0,1.31,0.025):
    j=np.argmin(abs(t-tt)); print(f'{t[j]:.3f} f0={f0[j]:7.1f} A1={a0[j]:6.1f} dBFS')
print('f0 min/max', f0[ok].min(), f0[ok].max(), t[ok][f0[ok].argmax()])
np.save('analisis/f0.npy',np.vstack([t,f0,a0]))
