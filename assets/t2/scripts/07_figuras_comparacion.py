import numpy as np, matplotlib, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'analisis'); from medir import cargar,f0track,niveles
from scipy.signal import stft
exec(open('/tmp/claude-0/figs.py').read().split('# FIG 1')[0].split("fs,y=wavfile")[0])
SRC=[('Original','comparacion/1_original_-23LUFS.wav',INK),('Aditiva','comparacion/2_aditiva_-23LUFS.wav',B),('FM','comparacion/3_fm_-23LUFS.wav',O)]
data=[]
for n,p,c in SRC:
    fs,y=cargar(p); t,f=f0track(fs,y); T,H,Nz=niveles(fs,y,t,f); data.append((n,c,fs,y,t,f,T,H,Nz))
# FIG 10 spectrograms same settings
fig,ax=plt.subplots(3,1,figsize=(10,8.6),sharex=True)
for a_,(n,c,fs,y,*_ ) in zip(ax,data):
    fq,tt,Z=stft(y,fs,window='hann',nperseg=2048,noverlap=2048-256,boundary=None,padded=False)
    S=20*np.log10(np.abs(Z)*2+1e-12)
    im=a_.pcolormesh(tt,fq/1000,S,shading='auto',cmap='magma',vmin=-110,vmax=-30,rasterized=True)
    a_.set_ylim(0,12); a_.grid(False); a_.set_ylabel('Frecuencia (kHz)')
    a_.set_title(f'{n} · −23 LUFS',loc='left',fontsize=11,color=INK)
ax[-1].set_xlabel('Tiempo (s)')
cb=fig.colorbar(im,ax=ax,shrink=0.5,pad=0.01); cb.set_label('dBFS')
fig.suptitle('Mismos ajustes en los tres: Hann 2048 muestras (42,7 ms), salto 256, escala −110 a −30 dBFS',x=0.07,ha='left',fontsize=10,color=SEC,y=0.995)
fig.savefig('figuras/10_comparacion_espectrogramas.png',bbox_inches='tight'); plt.close()
# FIG 11 harmonic profile in the meseta
fig,axs=plt.subplots(1,2,figsize=(10,3.9),sharey=True)
for a_,(lab,(t1,t2)) in zip(axs,[('Pico de altura (0,15–0,40 s)',(0.15,0.40)),('Meseta (0,55–0,80 s)',(0.55,0.80))]):
    for n,c,fs,y,t,f,T,H,Nz in data:
        m=(T>t1)&(T<t2); rel=np.median(H[m]-H[m][:,[0]],axis=0)[:10]
        a_.plot(range(1,11),rel,'-o',color=c,lw=2,ms=5,label=n)
    a_.set_xticks(range(1,11)); a_.set_xlabel('Armónico k'); a_.set_title(lab,loc='left',fontsize=11,color=INK)
    a_.set_ylim(-95,5)
axs[0].set_ylabel('dB respecto a la fundamental'); axs[0].legend(frameon=False,loc='lower left',fontsize=9)
fig.tight_layout(); fig.savefig('figuras/11_comparacion_perfil_armonico.png'); plt.close()
# FIG 12 envelope and f0
fig,ax=plt.subplots(2,1,figsize=(10,5.6),sharex=True)
for n,c,fs,y,t,f,T,H,Nz in data:
    w=int(0.01*fs); r=np.sqrt(np.convolve(y**2,np.ones(w)/w,'same')); tt=np.arange(len(y))/fs
    ax[0].plot(tt[::48],20*np.log10(r[::48]+1e-9),color=c,lw=1.5 if n!='Original' else 2.2,label=n,alpha=0.95)
    ok=(t>0.04)&(t<1.27); ax[1].plot(t[ok][::48],f[ok][::48],color=c,lw=1.5 if n!='Original' else 2.2,label=n)
ax[0].set_ylim(-60,-10); ax[0].set_ylabel('RMS 10 ms (dBFS)'); ax[0].set_title('Envolvente de amplitud',loc='left',fontsize=11,color=INK)
ax[0].legend(frameon=False,ncol=3,fontsize=9,loc='lower center')
ax[1].set_ylabel('f0 (Hz)'); ax[1].set_xlabel('Tiempo (s)'); ax[1].set_title('Trayectoria de la fundamental',loc='left',fontsize=11,color=INK); ax[1].set_ylim(500,1150)
ax[1].set_xlim(0,1.302)
fig.tight_layout(); fig.savefig('figuras/12_comparacion_envolvente_y_f0.png'); plt.close()
for n,c,fs,y,t,f,T,H,Nz in data:
    m=(T>0.55)&(T<0.8); print(n, np.round(np.median(H[m]-H[m][:,[0]],axis=0)[:10],1), 'ruido', round(np.median(Nz[m]-H[m,0]),1))
