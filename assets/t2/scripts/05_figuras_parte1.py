import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import stft
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
 'axes.edgecolor':'#8a8984','axes.labelcolor':'#0b0b0b','xtick.color':'#52514e','ytick.color':'#52514e',
 'axes.grid':True,'grid.color':'#e6e5e0','grid.linewidth':0.6,'savefig.dpi':170,'figure.facecolor':'white'})
B='#2a78d6';O='#eb6834';A='#1baf7a';INK='#0b0b0b';SEC='#52514e'
fs,y=wavfile.read('gibon_original_recortado.wav'); y=y/32768.0; t=np.arange(len(y))/fs
te,e=np.load('analisis/env.npy'); t0,f0,_=np.load('analisis/f0.npy')
ok=(t0>0.03)&(t0<1.285)
# FIG 1 waveform + envelope
fig,ax=plt.subplots(2,1,figsize=(10,5.2),sharex=True,gridspec_kw={'height_ratios':[1.2,1]})
ax[0].plot(t,y,color=B,lw=0.4); ax[0].set_ylabel('Amplitud'); ax[0].set_ylim(-0.7,0.7)
ax[0].set_title('Forma de onda: gibon_original.wav (48 kHz, 16 bit, mono, 1,302 s, pico −4,2 dBFS)',loc='left',fontsize=11,color=INK)
edb=20*np.log10(e+1e-9)
ax[1].plot(te,edb,color=B,lw=1.6); ax[1].set_ylabel('Envolvente RMS (dBFS)'); ax[1].set_ylim(-60,-5)
ax[1].set_xlabel('Tiempo (s)'); ax[1].set_title('Envolvente de amplitud (RMS, ventana de 10 ms)',loc='left',fontsize=11,color=INK)
for a,b,lab in [(0,0.10,'entrada'),(0.10,0.45,'pulsos rápidos'),(0.45,1.10,'olas lentas'),(1.10,1.302,'extinción')]:
    ax[1].axvspan(a,b,color='#f2f1ed' if lab in('entrada','olas lentas') else 'white',zorder=0)
    ax[1].text((a+b)/2,-57,lab,ha='center',color=SEC,fontsize=9)
ax[1].set_xlim(0,1.302)
fig.tight_layout(); fig.savefig('figuras/01_forma_de_onda_y_envolvente.png'); plt.close()
# FIG 2 zooms 20 ms at two moments
fig,ax=plt.subplots(1,2,figsize=(10,3.2),sharey=True)
for a_,tc in zip(ax,[0.25,0.70]):
    m=(t>=tc)&(t<tc+0.02); a_.plot((t[m]-tc)*1000,y[m],color=B,lw=1.2)
    fz=np.interp(tc+0.01,t0,f0); n=0.02*fz
    a_.set_title(f'20 ms desde {tc:.2f} s: ≈{n:.1f} ciclos → f0 ≈ {fz:.0f} Hz'.replace('.',','),loc='left',fontsize=10.5,color=INK)
    a_.set_xlabel('Tiempo dentro de la ventana (ms)')
ax[0].set_ylabel('Amplitud')
fig.tight_layout(); fig.savefig('figuras/02_zoom_20ms_dos_momentos.png'); plt.close()
# spectrogram helper
def spec(sig,N,hop=None):
    hop=hop or N//8
    f,tt,Z=stft(sig,fs,window='hann',nperseg=N,noverlap=N-hop,boundary=None,padded=False)
    S=20*np.log10(np.abs(Z)*2+1e-12); return f,tt+0,S
def showspec(ax,sig,N,title,fmax=12000,vmax=None):
    f,tt,S=spec(sig,N); vmax=vmax if vmax is not None else S.max()
    im=ax.pcolormesh(tt,f/1000,S,shading='auto',cmap='magma',vmin=vmax-80,vmax=vmax,rasterized=True)
    ax.set_ylim(0,fmax/1000); ax.set_ylabel('Frecuencia (kHz)'); ax.grid(False)
    ax.set_title(title,loc='left',fontsize=10.5,color=INK); return im
# FIG 3 spectrogram main + f0
fig,ax=plt.subplots(2,1,figsize=(10,6.4),sharex=True,gridspec_kw={'height_ratios':[1.6,1]})
im=showspec(ax[0],y,2048,'Espectrograma · ventana Hann de 2048 muestras (42,7 ms), salto 256, rango 80 dB')
cb=fig.colorbar(im,ax=ax,shrink=0.55,pad=0.01); cb.set_label('dB (relativo)')
ax[1].plot(t0[ok],f0[ok],color=B,lw=1.8); ax[1].set_ylabel('f0 (Hz)'); ax[1].set_xlabel('Tiempo (s)')
ax[1].set_title('Trayectoria de la fundamental (pico del espectro, interpolado)',loc='left',fontsize=10.5,color=INK)
for tt_,ff,lab in [(0.03,595,'≈595 Hz'),(0.262,1065,'máx. ≈1065 Hz'),(0.70,830,'meseta ≈830 Hz'),(1.20,680,'final ≈680 Hz')]:
    ax[1].annotate(lab,(tt_,ff),xytext=(4,8),textcoords='offset points',fontsize=9,color=INK)
    ax[1].plot(tt_,ff,'o',ms=4,color=B)
ax[1].set_ylim(500,1150); ax[1].set_xlim(0,1.302)
fig.savefig('figuras/03_espectrograma_y_f0.png',bbox_inches='tight'); plt.close()
# FIG 4 window sizes
fig,ax=plt.subplots(3,1,figsize=(10,7.5),sharex=True)
for a_,N in zip(ax,[512,2048,8192]):
    showspec(a_,y,N,f'Ventana de {N} muestras = {N/fs*1000:.1f} ms · resolución ≈ {fs/N:.1f} Hz'.replace('.',','),fmax=6000)
ax[-1].set_xlabel('Tiempo (s)')
fig.tight_layout(); fig.savefig('figuras/04_comparacion_de_ventanas.png'); plt.close()
# FIG 5 spectra at instants
def spectrum(tc,dur=0.06):
    a=int((tc-dur/2)*fs); s=y[a:a+int(dur*fs)]; w=np.hanning(len(s))
    S=np.abs(np.fft.rfft(s*w,65536))*2/w.sum(); F=np.fft.rfftfreq(65536,1/fs); return F,20*np.log10(S+1e-12)
fig,ax=plt.subplots(3,1,figsize=(10,8),sharex=True)
for a_,(tc,lab,c) in zip(ax,[(0.25,'Pico de altura (0,25 s): el momento más brillante',B),(0.70,'Meseta (0,70 s)',A),(1.20,'Extinción (1,20 s): el momento más opaco',O)]):
    F,S=spectrum(tc); a_.plot(F/1000,S,color=c,lw=0.9)
    fz=np.interp(tc,t0,f0)
    for h in range(1,11):
        m=(F>h*fz*0.96)&(F<h*fz*1.04); i=np.argmax(S[m]); fh=F[m][i]; sh=S[m][i]
        a_.plot(fh/1000,sh,'o',ms=4,color=c); 
        if h<=8: a_.text(fh/1000,sh+3,f'{h}',ha='center',fontsize=8,color=SEC)
    a_.set_ylim(-110,0); a_.set_ylabel('dBFS'); a_.set_title(lab+f' · f0 ≈ {fz:.0f} Hz · ventana Hann de 60 ms',loc='left',fontsize=10.5,color=INK)
ax[-1].set_xlim(0,12); ax[-1].set_xlabel('Frecuencia (kHz) · los números marcan el armónico k (k·f0)')
fig.tight_layout(); fig.savefig('figuras/05_espectros_en_tres_instantes.png'); plt.close()
# FIG 6 harmonic levels relative to H1 over time
D=np.load('analisis/harm.npy'); T=D[:,0]; H=D[:,1:13]; Nz=D[:,13]
m=(T>0.05)&(T<1.28)
rel=H[m]-H[m][:,[0]]
def smooth(v,k=5): return np.convolve(v,np.ones(k)/k,'same')
hi=10*np.log10(np.mean(10**(rel[:,2:8]/10),axis=1))
fig,ax=plt.subplots(figsize=(10,3.8))
ax.plot(T[m],smooth(rel[:,1]),color=B,lw=2,label='2.º armónico')
ax.plot(T[m],smooth(hi),color=O,lw=2,label='armónicos 3 a 8 (promedio de energía)')
ax.plot(T[m],smooth(Nz[m]-H[m][:,0]),color=A,lw=2,label='ruido entre armónicos (1,5–12 kHz)')
ax.set_ylabel('dB respecto a la fundamental'); ax.set_xlabel('Tiempo (s)'); ax.set_ylim(-80,-10)
ax.set_title('Cuánto más débil que la fundamental es cada zona del espectro',loc='left',fontsize=11,color=INK)
ax.legend(frameon=False,loc='lower left',ncol=3,fontsize=9); ax.set_xlim(0,1.302)
fig.tight_layout(); fig.savefig('figuras/06_niveles_relativos_en_el_tiempo.png'); plt.close()
print('ok')
