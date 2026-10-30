import numpy as np, matplotlib, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
exec(open('/tmp/claude-0/figs.py').read().split('# FIG 1')[0].split("fs,y=wavfile")[0])
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert
def env(s,fs): w=int(0.005*fs); return 20*np.log10(np.sqrt(np.convolve(s**2,np.ones(w)/w,'same'))+1e-9)
def f0(s,fs,lo,hi):
    sos=butter(6,[lo,hi],'band',fs=fs,output='sos'); a=hilbert(sosfiltfilt(sos,s))
    i=np.diff(np.unwrap(np.angle(a)))*fs/(2*np.pi); k=int(0.01*fs); return np.convolve(i,np.ones(k)/k,'same')
fig,ax=plt.subplots(4,1,figsize=(10,9.4),sharex=True)
off=None
for a_,(n,lab) in zip(ax[:3],[('normal','Ataque 8 ms · liberación 150 ms (ajuste propuesto)'),('rapido','Ataque 1 ms · liberación 20 ms'),('lento','Ataque 60 ms · liberación 800 ms')]):
    fs,x=wavfile.read(f'render/sim_vivo_{n}.wav'); L=x[:,0]/32768; R=x[:,1]/32768
    t=np.arange(len(L))/fs; s=np.argmax(np.abs(L)>0.01)/fs-0.3
    m=(t>=s)&(t<s+3.4)
    a_.plot(t[m][::24]-s,env(L,fs)[m][::24],color=SEC,lw=1.4,label='entrada: silbido (L)')
    a_.plot(t[m][::24]-s,env(R,fs)[m][::24],color=O,lw=1.8,label='salida: modelo FM (R)')
    a_.set_ylim(-80,0); a_.set_ylabel('RMS 5 ms (dBFS)'); a_.set_title(lab,loc='left',fontsize=10.5,color=INK)
    if n=='normal':
        a_.legend(frameon=False,ncol=2,fontsize=9,loc='lower center')
        fL=f0(L,fs,600,1500); fR=f0(R,fs,500,1300); ss=(t[:-1]>=s)&(t[:-1]<s+3.4)
        act=(env(L,fs)[:-1]>-35)
        ax[3].plot(t[:-1][ss&act][::24]-s,fL[ss&act][::24],'.',ms=1.5,color=SEC,label='silbido')
        actR=(env(R,fs)[:-1]>-45)
        ax[3].plot(t[:-1][ss&actR][::24]-s,fR[ss&actR][::24],'.',ms=1.5,color=O,label='modelo (−2 semitonos)')
ax[3].set_ylim(700,1100); ax[3].set_ylabel('f0 (Hz)'); ax[3].set_xlabel('Tiempo (s)')
ax[3].set_title('Altura: el modelo copia la del silbido, transpuesta',loc='left',fontsize=10.5,color=INK)
ax[3].legend(frameon=False,fontsize=9,markerscale=6,loc='lower right')
fig.suptitle('Prueba de la cadena de escucha con tu silbido grabado (dos veces, con pausas). No reemplaza la toma en vivo.',x=0.02,ha='left',fontsize=10.5,color=INK)
fig.tight_layout(); fig.savefig('figuras/13_prueba_cadena_de_escucha.png'); plt.close()
