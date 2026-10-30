// ============================================================================
// common.js — partes compartidas por los dos modelos (aditiva y FM)
// Tarea 2 · Métodos de síntesis · IEE2003 Orquesta de Laptops UC
// Todo corre con la Web Audio API nativa de Chrome: no hay librerías externas.
// ============================================================================

// ---------------------------------------------------------------------------
// 1. LA PARTITURA DE CONTROL
// Son los contornos del gesto del gibón, medidos en el análisis de la Parte 1
// y simplificados a pocos puntos de quiebre (entre ellos se interpola).
// No contienen audio de la grabación: solo números de altura y volumen.
// ---------------------------------------------------------------------------
const PARTITURA = {
  duracion: 1.302, // segundos (duración de la grabación original)
  // Altura de la fundamental: [tiempo (s), frecuencia (Hz)].
  // Sube ~10 semitonos al inicio, baja a una meseta de ~830 Hz y cae al final.
  altura: [
    [0.000, 590], [0.030, 590], [0.085, 648], [0.115, 747], [0.135, 854],
    [0.150, 891], [0.170, 999], [0.255, 1064], [0.280, 1050], [0.310, 985],
    [0.385, 995], [0.400, 964], [0.415, 891], [0.450, 854], [0.515, 860],
    [0.550, 826], [0.785, 823], [0.875, 853], [1.065, 762], [1.120, 687],
    [1.210, 697], [1.270, 675], [1.302, 675]
  ],
  // Envolvente lenta de amplitud: [tiempo (s), nivel (dBFS, RMS en 40 ms)].
  amplitud: [
    [0.000, -60], [0.010, -42.6], [0.025, -29.4], [0.055, -19.3], [0.110, -13.4],
    [0.180, -13.5], [0.235, -8.6], [0.330, -16.5], [0.440, -14.0], [0.460, -18.9],
    [0.505, -17.8], [0.550, -12.5], [0.615, -20.8], [0.670, -11.7], [0.730, -16.6],
    [0.790, -12.4], [0.820, -15.9], [0.860, -27.2], [0.885, -16.4], [0.910, -12.4],
    [1.065, -12.7], [1.105, -18.1], [1.145, -15.1], [1.255, -22.2], [1.275, -27.2],
    [1.302, -60]
  ],
  // Pulsos rápidos de volumen (modulación de amplitud) medidos entre 0,09 y 0,45 s:
  // empiezan cerca de 75 por segundo y se frenan hasta cerca de 27 por segundo.
  pulsos: { inicio: 0.09, fin: 0.45, tasaInicial: 75, tasaFinal: 27 },
  fRef: 830 // Hz: la meseta, usada como referencia del parámetro "f0 base"
};

// Interpolación lineal en una lista de puntos [x, y].
function interp(puntos, x) {
  if (x <= puntos[0][0]) return puntos[0][1];
  for (let i = 1; i < puntos.length; i++) {
    if (x <= puntos[i][0]) {
      const [x0, y0] = puntos[i - 1], [x1, y1] = puntos[i];
      return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
    }
  }
  return puntos[puntos.length - 1][1];
}

// ---------------------------------------------------------------------------
// 2. CURVAS DE CONTROL
// Convierte la partitura + los parámetros del usuario en curvas muestreadas
// (200 valores por segundo) que luego se cargan en los AudioParam con
// setValueCurveAtTime. Ambas síntesis usan exactamente las mismas curvas.
//   p.f0        f0 base (Hz): altura de la meseta
//   p.contorno  % del contorno de altura medido (0 = altura fija)
//   p.estirar   factor de duración (2 = el doble de largo)
//   p.pulsos    % de profundidad de los pulsos rápidos
//   p.tasa      multiplicador de la tasa de pulsos medida
// ---------------------------------------------------------------------------
const PUNTOS_POR_SEG = 200;
function curvas(p) {
  const D = PARTITURA.duracion * p.estirar;
  const n = Math.max(2, Math.round(D * PUNTOS_POR_SEG) + 1);
  const f0 = new Float32Array(n), amp = new Float32Array(n);
  const tasa = new Float32Array(n), prof = new Float32Array(n);
  const ampMax = Math.pow(10, -8.6 / 20); // máximo de la envolvente medida
  const { inicio, fin, tasaInicial, tasaFinal } = PARTITURA.pulsos;
  for (let i = 0; i < n; i++) {
    const tp = (i / (n - 1)) * PARTITURA.duracion; // tiempo en la partitura original
    // Altura: desviación en semitonos respecto de la meseta, escalada por "contorno".
    const st = 12 * Math.log2(interp(PARTITURA.altura, tp) / PARTITURA.fRef);
    f0[i] = p.f0 * Math.pow(2, (st * p.contorno / 100) / 12);
    // Amplitud: dB -> lineal, normalizada para que el máximo valga 1.
    amp[i] = Math.pow(10, interp(PARTITURA.amplitud, tp) / 20) / ampMax;
    // Pulsos: la tasa baja de forma exponencial de 75 a 27 Hz dentro de la ventana.
    const u = Math.min(1, Math.max(0, (tp - inicio) / (fin - inicio)));
    tasa[i] = p.tasa * tasaInicial * Math.pow(tasaFinal / tasaInicial, u);
    // Profundidad con rampas de 20 ms en los bordes de la ventana.
    const borde = Math.min(1, Math.max(0, Math.min(tp - inicio, fin - tp) / 0.02));
    prof[i] = (p.pulsos / 100) * borde;
  }
  return { D, n, f0, amp, tasa, prof };
}

// ---------------------------------------------------------------------------
// 3. MODULACIÓN DE AMPLITUD (los pulsos), común a ambos modelos.
// ganancia(t) = 1 - d/2 + (d/2)·sin(2π·tasa·t)
// Con d = 1 el volumen oscila entre 0 y 1: pulsos completos.
// ---------------------------------------------------------------------------
function crearPulsos(ctx, c, t0, nodos) {
  const trem = ctx.createGain();
  trem.gain.value = 0;
  const base = new Float32Array(c.n), mitad = new Float32Array(c.n);
  for (let i = 0; i < c.n; i++) { base[i] = 1 - c.prof[i] / 2; mitad[i] = c.prof[i] / 2; }
  trem.gain.setValueCurveAtTime(base, t0, c.D);
  const lfo = ctx.createOscillator();
  lfo.frequency.setValueCurveAtTime(c.tasa, t0, c.D);
  const prof = ctx.createGain();
  prof.gain.value = 0;
  prof.gain.setValueCurveAtTime(mitad, t0, c.D);
  lfo.connect(prof).connect(trem.gain); // la señal del LFO se suma a la ganancia
  lfo.start(t0); lfo.stop(t0 + c.D + 0.05);
  nodos.push(lfo);
  return trem;
}

// ---------------------------------------------------------------------------
// 4. UTILIDADES
// ---------------------------------------------------------------------------
// Generador pseudoaleatorio con semilla: el ruido es idéntico en cada render,
// así los audios entregados se pueden reproducir exactamente.
function rng(semilla) {
  let s = semilla >>> 0;
  return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return (((t ^ (t >>> 14)) >>> 0) / 4294967296) * 2 - 1; };
}
function bufferRuido(ctx, segundos, semilla) {
  const b = ctx.createBuffer(1, Math.ceil(segundos * ctx.sampleRate), ctx.sampleRate);
  const d = b.getChannelData(0), r = rng(semilla);
  for (let i = 0; i < d.length; i++) d[i] = r();
  return b;
}

// Codifica un AudioBuffer (1 o 2 canales) como WAV PCM de 16 bit.
function aWav(canales, sr) {
  const n = canales[0].length, nc = canales.length, bytes = 44 + n * nc * 2;
  const v = new DataView(new ArrayBuffer(bytes));
  const txt = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  txt(0, 'RIFF'); v.setUint32(4, bytes - 8, true); txt(8, 'WAVE'); txt(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, nc, true);
  v.setUint32(24, sr, true); v.setUint32(28, sr * nc * 2, true); v.setUint16(32, nc * 2, true);
  v.setUint16(34, 16, true); txt(36, 'data'); v.setUint32(40, n * nc * 2, true);
  let o = 44;
  for (let i = 0; i < n; i++) for (let c = 0; c < nc; c++) {
    const x = Math.max(-1, Math.min(1, canales[c][i]));
    v.setInt16(o, x < 0 ? x * 32768 : x * 32767, true); o += 2;
  }
  return new Blob([v], { type: 'audio/wav' });
}
function descargar(blob, nombre) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = nombre; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

// ---------------------------------------------------------------------------
// 5. INTERFAZ: deslizadores, tocar, exportar, ajustes en JSON y espectrograma.
// MODELO debe definir: nombre, archivo, parametros (lista), construir(ctx, p, t0, salida)
// ---------------------------------------------------------------------------
const SR = 48000;
let ctxVivo = null, nodosSonando = [], analizador = null;
const valores = {};

function ajustesGibon() {
  const p = {}; MODELO.parametros.forEach(q => p[q.id] = q.def); return p;
}

function armarInterfaz() {
  const cont = document.getElementById('controles');
  MODELO.parametros.forEach(q => {
    const fila = document.createElement('div'); fila.className = 'fila';
    fila.innerHTML = `<label for="${q.id}"><b>${q.nombre}</b><span>${q.unidad}</span></label>
      <input type="range" id="${q.id}" min="${q.min}" max="${q.max}" step="${q.paso}">
      <input type="number" id="${q.id}_n" min="${q.min}" max="${q.max}" step="${q.paso}">`;
    cont.appendChild(fila);
    const r = fila.querySelector('input[type=range]'), num = fila.querySelector('input[type=number]');
    const fijar = x => { valores[q.id] = +x; r.value = x; num.value = x; mostrarJSON(); };
    r.oninput = () => fijar(r.value); num.onchange = () => fijar(num.value);
    q.fijar = fijar;
  });
  const tb = document.querySelector('#tabla tbody');
  MODELO.parametros.forEach(q => {
    tb.insertAdjacentHTML('beforeend', `<tr><td>${q.nombre}</td><td>${q.min} a ${q.max}</td><td>${q.unidad}</td><td>${q.def}</td><td>${q.efecto}</td></tr>`);
  });
  cargar(ajustesGibon());
  document.getElementById('tocar').onclick = tocar;
  document.getElementById('detener').onclick = detener;
  document.getElementById('exportar').onclick = exportar;
  document.getElementById('gibon').onclick = () => cargar(ajustesGibon());
  document.getElementById('aplicar').onclick = () => {
    try { cargar(JSON.parse(document.getElementById('json').value)); }
    catch (e) { alert('El texto no es un JSON válido.'); }
  };
}
function cargar(p) { MODELO.parametros.forEach(q => q.fijar(p[q.id] ?? q.def)); }
function mostrarJSON() { document.getElementById('json').value = JSON.stringify(valores); }

function asegurarContexto() {
  if (!ctxVivo) {
    ctxVivo = new AudioContext({ sampleRate: SR });
    analizador = ctxVivo.createAnalyser(); analizador.fftSize = 2048;
    analizador.smoothingTimeConstant = 0; analizador.connect(ctxVivo.destination);
    dibujarEspectrograma();
  }
  ctxVivo.resume();
  return ctxVivo;
}
function tocar() {
  asegurarContexto(); detener();
  nodosSonando = MODELO.construir(ctxVivo, { ...valores }, ctxVivo.currentTime + 0.05, analizador);
}
function detener() { nodosSonando.forEach(n => { try { n.stop(); } catch (e) {} }); nodosSonando = []; }

// Render sin tiempo real (OfflineAudioContext): mismo grafo, resultado exacto.
async function renderizar(p, colaSeg = 0.3) {
  const D = PARTITURA.duracion * p.estirar;
  const ctx = new OfflineAudioContext(1, Math.ceil((D + colaSeg) * SR), SR);
  MODELO.construir(ctx, p, 0, ctx.destination);
  const buf = await ctx.startRendering();
  return aWav([buf.getChannelData(0)], SR);
}
async function exportar() {
  const blob = await renderizar({ ...valores });
  descargar(blob, `${MODELO.archivo}_${Date.now()}.wav`);
}
// Para automatizar renders desde fuera (devuelve el WAV en base64).
window.renderBase64 = async (p, cola) => {
  const b = await renderizar({ ...ajustesGibon(), ...p }, cola);
  const u8 = new Uint8Array(await b.arrayBuffer()); let s = '';
  for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
  return btoa(s);
};

// Espectrograma en vivo de lo que suena (0 a 12 kHz, escala de color en dB).
function dibujarEspectrograma() {
  const cv = document.getElementById('espectro'), g = cv.getContext('2d');
  const datos = new Float32Array(analizador.frequencyBinCount);
  const binMax = Math.round(12000 / (SR / analizador.fftSize));
  function color(db) {
    const x = Math.min(1, Math.max(0, (db + 110) / 90));
    const r = Math.round(255 * Math.min(1, x * 1.6)), gg = Math.round(255 * Math.max(0, x * 1.6 - 0.6)), b = Math.round(255 * Math.max(0, Math.min(1, 0.45 - x) * 1.6 + Math.max(0, x - 0.85) * 4));
    return `rgb(${r},${gg},${b})`;
  }
  (function paso() {
    analizador.getFloatFrequencyData(datos);
    g.drawImage(cv, -2, 0);
    for (let y = 0; y < cv.height; y++) {
      const bin = Math.round((1 - y / cv.height) * binMax);
      g.fillStyle = color(datos[bin]); g.fillRect(cv.width - 2, y, 2, 1);
    }
    requestAnimationFrame(paso);
  })();
}
