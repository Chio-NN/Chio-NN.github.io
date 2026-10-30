# Genera los diagramas de flujo de señal como SVG (se insertan en las páginas
# y se exportan como PNG para el portafolio).
def caja(x, y, w, h, l1, l2='', acento=False):
    cls = 'caja acento' if acento else 'caja'
    s = f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    if l2:
        s += f'<text class="t1" x="{x+w/2}" y="{y+h/2-4}">{l1}</text><text class="t2" x="{x+w/2}" y="{y+h/2+13}">{l2}</text>'
    else:
        s += f'<text class="t1" x="{x+w/2}" y="{y+h/2+5}">{l1}</text>'
    return s

def flecha(pts, etiqueta=None, ex=0, ey=-6):
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
    s = f'<path class="fl" d="{d}" marker-end="url(#pt)"/>'
    if etiqueta:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        s += f'<text class="t3" x="{(x0+x1)/2+ex}" y="{(y0+y1)/2+ey}">{etiqueta}</text>'
    return s

def svg(w, h, titulo, cuerpo):
    return f'''<svg viewBox="0 0 {w} {h}" role="img" aria-label="{titulo}" xmlns="http://www.w3.org/2000/svg">
<style>
.caja{{fill:var(--sup,#fff);stroke:var(--linea,#8a8984);stroke-width:1.25}}
.acento{{fill:var(--acento-suave,#e3eefb);stroke:var(--acento,#2a78d6);stroke-width:2}}
.t1{{font:600 13px system-ui,sans-serif;fill:var(--tinta,#0b0b0b);text-anchor:middle}}
.t2{{font:11.5px system-ui,sans-serif;fill:var(--tinta2,#52514e);text-anchor:middle}}
.t3{{font:11.5px system-ui,sans-serif;fill:var(--tinta2,#52514e);text-anchor:middle}}
.tt{{font:600 15px system-ui,sans-serif;fill:var(--tinta,#0b0b0b)}}
.fl{{fill:none;stroke:var(--linea,#8a8984);stroke-width:1.25}}
</style>
<defs><marker id="pt" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--linea,#8a8984)"/></marker></defs>
<text class="tt" x="16" y="26">{titulo}</text>
{cuerpo}
</svg>'''

def aditiva():
    W, H = 150, 46
    b = ''
    b += caja(16, 50, 196, 52, 'Partitura medida', 'f0(t) · envolvente a(t)')
    rows = [(130, 'Seno k = 1', 'f0(t) · nivel 1'), (190, 'Seno k = 2', '2·f0(t) · −26 dB'),
            (250, 'Senos k = 3 … N', 'k·f0(t) · brillo − 1,5 dB/k'), (322, 'Ruido blanco', 'semilla fija')]
    for y, a, c in rows:
        b += caja(16, y, 196, H, a, c)
    b += caja(260, 322, 150, H, 'Pasa banda', '5 kHz · Q 0,7', acento=True)
    b += caja(440, 322, 120, H, '× ruido', 'dB re f0')
    b += caja(470, 190, 70, H, 'Σ', '')
    for y, *_ in rows[:3]:
        b += flecha([(212, y + 23), (440, y + 23), (440, 213), (470, 213)] if y != 190 else [(212, 213), (470, 213)])
    b += flecha([(212, 345), (260, 345)]); b += flecha([(410, 345), (440, 345)])
    b += flecha([(500, 322), (500, 236)])
    b += caja(590, 190, 150, H, '× envolvente', 'a(t) medida')
    b += caja(590, 262, 150, H, '× pulsos (AM)', '1 − d/2 + d/2·sen')
    b += caja(590, 334, 150, H, 'LFO 75 → 27 Hz', '× tasa · prof. d')
    b += caja(780, 190, 110, H, '× 0,5', 'salida', acento=False)
    b += flecha([(540, 213), (590, 213)]); b += flecha([(665, 236), (665, 262)])
    b += flecha([(665, 334), (665, 308)])
    b += flecha([(740, 285), (760, 285), (760, 213), (780, 213)])
    b += flecha([(60, 102), (60, 130)])
    b += f'<text class="t3" x="150" y="121">k·f0(t) en cada seno</text>'
    b += flecha([(212, 76), (665, 76), (665, 190)])
    b += f'<text class="t3" x="700" y="140">a(t)</text>'
    return svg(910, 400, 'Modelo A · Síntesis aditiva: un seno por armónico, más ruido filtrado', b)

def fm():
    W, H = 150, 46
    b = ''
    b += caja(16, 50, 196, 52, 'Partitura medida', 'f0(t) · envolvente a(t)')
    b += caja(16, 140, 196, H, 'Moduladora', 'seno · fm = razón·f0(t)')
    b += caja(250, 140, 170, H, '× desviación', 'I·a(t)·fm  (Hz)')
    b += caja(460, 140, 60, H, '+', '')
    b += caja(250, 60, 170, H, 'f0(t)', 'frecuencia base')
    b += caja(560, 140, 160, H, 'Portadora', 'seno · fc = f0(t) + desv.')
    b += flecha([(212, 163), (250, 163)]); b += flecha([(420, 163), (460, 163)])
    b += flecha([(420, 83), (490, 83), (490, 140)]); b += flecha([(520, 163), (560, 163)])
    b += flecha([(212, 76), (250, 76)])
    b += caja(560, 230, 160, H, '× envolvente', 'a(t) medida')
    b += caja(560, 300, 160, H, '× pulsos (AM)', 'LFO 75 → 27 Hz')
    b += caja(342, 300, 196, H, 'Filtros', 'pasa altos 20 Hz · pasa bajos', acento=True)
    b += caja(160, 260, 150, H, 'Seco', '× (1 − r)')
    b += caja(160, 340, 150, H, 'Convolución', 'IR sintética 0,6 s', acento=True)
    b += caja(30, 300, 80, H, 'Σ · 0,5', 'salida')
    b += flecha([(640, 186), (640, 230)]); b += flecha([(640, 276), (640, 300)])
    b += flecha([(560, 323), (538, 323)])
    b += flecha([(342, 323), (326, 323), (326, 283), (310, 283)])
    b += flecha([(326, 323), (326, 363), (310, 363)])
    b += flecha([(160, 283), (135, 283), (135, 315), (110, 315)])
    b += flecha([(160, 363), (135, 363), (135, 331), (110, 331)])
    b += f'<text class="t3" x="235" y="406">r = reverberación (%)</text>'
    return svg(750, 420, 'Modelo B · Síntesis FM: una moduladora mueve la frecuencia de la portadora', b)

def escucha():
    H = 46
    b = ''
    b += caja(16, 60, 130, H, 'Micrófono', 'silbido, sin AGC')
    b += caja(180, 60, 120, H, '× ganancia', 'dB de entrada')
    b += caja(334, 60, 110, H, '|x|', 'rectificar')
    b += caja(478, 60, 220, H, 'Suavizado', 'ataque 8 ms · liberación 150 ms', acento=True)
    b += caja(730, 60, 130, H, 'e(t) ∈ [0, 1]', 'envolvente')
    b += caja(334, 160, 364, H, 'Detector de altura (YIN)', '400–4000 Hz · cada 512 muestras · suavizado 15 ms', acento=True)
    b += caja(730, 160, 130, H, '× 2^(transp/12)', 'transposición')
    b += caja(894, 60, 180, H, 'Volumen e índice', 'amp = e(t) · I = Imáx·e(t)')
    b += caja(894, 160, 180, H, 'Portadora fc', 'moduladora fm = razón·fc')
    b += flecha([(146, 83), (180, 83)]); b += flecha([(300, 83), (334, 83)])
    b += flecha([(444, 83), (478, 83)]); b += flecha([(698, 83), (730, 83)]); b += flecha([(860, 83), (894, 83)])
    b += flecha([(315, 83), (315, 183), (334, 183)]); b += flecha([(698, 183), (730, 183)]); b += flecha([(860, 183), (894, 183)])
    b += caja(894, 250, 180, H, 'Modelo FM', 'pasa bajos + convolución')
    b += flecha([(1074, 83), (1090, 83), (1090, 273), (1074, 273)])
    b += flecha([(984, 206), (984, 250)])
    b += caja(560, 250, 260, H, 'Grabación estéreo', 'L = micrófono · R = modelo')
    b += flecha([(894, 273), (820, 273)])
    b += flecha([(81, 106), (81, 273), (560, 273)])
    b += f'<text class="t3" x="420" y="322">la altura solo se actualiza si e(t) supera el umbral (dB)</text>'
    return svg(1110, 336, 'Parte 4 · Cadena de escucha: el silbido controla el modelo FM', b)
