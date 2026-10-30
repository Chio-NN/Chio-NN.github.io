import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert, find_peaks
fs,y=wavfile.read('gibon_original_recortado.wav'); y=y/32768.0
sos=butter(10,1130,'low',fs=fs,output='sos'); f1=sosfiltfilt(sos,y)
an=hilbert(f1); ph=np.unwrap(np.angle(an)); inst=np.diff(ph)*fs/(2*np.pi)
k=int(0.01*fs); inst_s=np.convolve(inst,np.ones(k)/k,'same')
amp1=np.abs(an)
t=np.arange(len(inst))/fs
for tt in np.arange(0.02,1.3,0.02): print(f'{tt:.2f} {inst_s[int(tt*fs)]:7.1f}  A1={20*np.log10(amp1[int(tt*fs)]+1e-9):6.1f}')
np.save('analisis/f0_hilbert.npy',np.vstack([t[::48],inst_s[::48],amp1[:-1][::48]]))
# pulse rate: envelope of full signal (hilbert amplitude of y, smoothed 3 ms)
env=np.abs(hilbert(y)); k=int(0.003*fs); env=np.convolve(env,np.ones(k)/k,'same')
seg=(np.arange(len(y))/fs>0.08)&(np.arange(len(y))/fs<0.45)
e=env[seg]; e=e-e.mean()
E=np.abs(np.fft.rfft(e*np.hanning(len(e)),2**18)); F=np.fft.rfftfreq(2**18,1/fs)
m=(F>5)&(F<200); print('env spectrum peaks 0.08-0.45:', sorted([(round(F[m][i],1),round(E[m][i],2)) for i in find_peaks(E[m],distance=200)[0]],key=lambda z:-z[1])[:6])
pk,_=find_peaks(env[seg],prominence=0.05,distance=int(0.006*fs))
tp=np.arange(len(y))[seg][pk]/fs; print('pulse times',np.round(tp,3)); print('intervals ms',np.round(np.diff(tp)*1000,1))
seg2=(np.arange(len(y))/fs>0.45)&(np.arange(len(y))/fs<1.1)
pk2,_=find_peaks(env[seg2],prominence=0.08,distance=int(0.05*fs)); print('slow wave peaks',np.round(np.arange(len(y))[seg2][pk2]/fs,3))
