import numpy as np, sys
sys.path.insert(0,'analisis')
from scipy.io import wavfile
from lufs import lufs
D=1.302; OBJ=-23.0
for src,dst in [('gibon_original_recortado.wav','comparacion/1_original_-23LUFS.wav'),('render/aditiva_gibon.wav','comparacion/2_aditiva_-23LUFS.wav'),('render/fm_gibon.wav','comparacion/3_fm_-23LUFS.wav')]:
    fs,y=wavfile.read(src); y=y.astype(float)/32768; y=y[:int(D*fs)]
    L=lufs(y,fs); g=10**((OBJ-L)/20); z=y*g
    wavfile.write(dst,fs,np.round(np.clip(z,-1,1)*32767).astype(np.int16))
    print(f'{src}: {L:.1f} LUFS -> ganancia {20*np.log10(g):+.1f} dB, pico final {20*np.log10(np.abs(z).max()):.1f} dBFS, verif {lufs(z,fs):.2f}')
