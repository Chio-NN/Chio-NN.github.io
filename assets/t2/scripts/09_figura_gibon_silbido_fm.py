import numpy as np, matplotlib, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'analisis'); from medir import niveles
exec(open('/tmp/claude-0/figs.py').read().split('# FIG 1')[0].split("fs,y=wavfile")[0])
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert
def prof(p,t1,t2,band):
    fs,y=wavfile.read(p); y=y/32768
    sos=butter(8,band,'band',fs=fs,output='sos'); a=hilbert(sosfiltfilt(sos,y))
    f=np.diff(np.unwrap(np.angle(a)))*fs/(2*np.pi); k=int(0.01*fs); f=np.convolve(f,np.ones(k)/k,'same'); t=np.arange(len(f))/fs
    T,H,Nz=niveles(fs,y,t,f); m=(T>t1)&(T<t2); return np.median(H[m]-H[m][:,[0]],0)[:8]
G=prof('gibon_original_recortado.wav',0.55,0.80,[500,1150]); S=prof('silbido.wav',0.1,0.85,[600,1500]); F=prof('render/fm_gibon.wav',0.55,0.80,[500,1150])
print(np.round(G,1),np.round(S,1),np.round(F,1))
fig,ax=plt.subplots(figsize=(10,3.8))
for v,c,l in [(G,INK,'Gibón (meseta)'),(S,A,'Tu silbido'),(F,O,'Modelo FM, ajuste «Gibón»')]:
    ax.plot(range(1,9),v,'-o',color=c,lw=2,ms=5,label=l)
ax.set_xticks(range(1,9)); ax.set_xlabel('Armónico k'); ax.set_ylabel('dB respecto a la fundamental'); ax.set_ylim(-100,5)
ax.set_title('El silbido es aún más puro que el gibón: casi solo fundamental',loc='left',fontsize=11,color=INK)
ax.legend(frameon=False,fontsize=9,loc='lower left'); fig.tight_layout(); fig.savefig('figuras/14_perfil_gibon_silbido_fm.png')
