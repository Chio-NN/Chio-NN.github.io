import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import diagramas as dg
S = pathlib.Path(__file__).parent
OUT = S.parent / 'sitio'; OUT.mkdir(exist_ok=True)
plant = (S / 'plantilla.html').read_text()
common = (S / 'common.js').read_text()

VIVO = '''
<h2>Parte 4 · Tocar el modelo FM con un silbido en vivo</h2>
<p><b>Ponte audífonos antes de activar el micrófono.</b> El silbido no se escucha: solo controla el modelo. Su envolvente (seguidor con ataque y liberación) maneja el volumen y el índice de modulación; su altura (detector YIN) maneja la frecuencia de la portadora, transpuesta. La razón, el índice, el corte y la reverberación se toman de los deslizadores de arriba.</p>
<div class="diagrama">{{DIAG_VIVO}}</div>
<div class="panel" id="controles-vivo" style="margin-top:12px"></div>
<div class="botones">
  <button class="principal" id="vivo-on">Activar micrófono</button>
  <button id="vivo-off">Detener</button>
  <button id="grabar">Grabar toma</button>
  <span class="nota" id="tiempo-toma" style="align-self:center">0:00</span>
</div>
<div class="medidor"><div id="medidor"></div></div>
<p class="nota"><span id="estado-vivo">Micrófono apagado.</span> <span id="altura-vivo"></span></p>
<p class="nota">La toma se descarga como WAV estéreo de 16 bit: canal izquierdo = micrófono (entrada), canal derecho = modelo (salida). Graba entre 1 y 2 minutos.</p>
'''.replace('{{DIAG_VIVO}}', dg.escucha())

def pagina(nombre, titulo, sub, diag, js, extra='', inicio='armarInterfaz();'):
    h = (plant.replace('{{TITULO}}', titulo).replace('{{SUBTITULO}}', sub)
         .replace('{{DIAGRAMA}}', diag).replace('{{EXTRA}}', extra)
         .replace('{{CODIGO}}', common + '\n' + js).replace('{{INICIO}}', inicio))
    (OUT / nombre).write_text(h)

pagina('aditiva.html', 'Modelo A · Síntesis aditiva',
       'Llamada de gibón construida parcial por parcial: un oscilador seno por armónico, cada uno con su volumen, más ruido filtrado.',
       dg.aditiva(), (S / 'aditiva.js').read_text())
pagina('fm.html', 'Modelo B · Síntesis FM',
       'Llamada de gibón construida de forma indirecta: una moduladora mueve la frecuencia de una portadora; los armónicos aparecen solos, con pesos que fija el índice.',
       dg.fm(), (S / 'fm.js').read_text() + '\n' + (S / 'live.js').read_text(), VIVO,
       'armarInterfaz(); armarVivo();')

(OUT / 'index.html').write_text('''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>T2 · Métodos de síntesis</title>
<style>:root{--fondo:#fcfcfb;--tinta:#0b0b0b;--tinta2:#52514e;--acento:#2a78d6;--rejilla:#e6e5e0}
@media (prefers-color-scheme:dark){:root{--fondo:#1a1a19;--tinta:#f0efec;--tinta2:#c3c2b7;--acento:#3987e5;--rejilla:#34332f}}
body{margin:0;background:var(--fondo);color:var(--tinta);font:16px/1.55 system-ui,sans-serif}main{max-width:720px;margin:0 auto;padding:32px 16px}
a{color:var(--acento)}li{margin:8px 0}p{color:var(--tinta2)}</style></head><body><main>
<h1>T2 · Métodos de síntesis</h1>
<p>IEE2003 Orquesta de Laptops UC · Fuente: llamada de gibón (1,302 s). Dos modelos en Web Audio API que corren en Chrome, sin instalar nada.</p>
<ul>
<li><a href="aditiva.html"><b>Modelo A · Síntesis aditiva</b></a>: un seno por armónico + ruido filtrado en pasa banda.</li>
<li><a href="fm.html"><b>Modelo B · Síntesis FM</b></a>: portadora + moduladora, pasa bajos y reverberación por convolución. Incluye el modo en vivo de la Parte 4 (silbido).</li>
</ul>
<p>Usa audífonos. Cada página documenta sus parámetros, su diagrama de flujo de señal y cómo reproducir los audios entregados.</p>
</main></body></html>''')
print('ok')
