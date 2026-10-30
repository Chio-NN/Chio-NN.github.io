// ============================================================================
// Parte 4 — EL MODELO FM TOCADO POR LA FUENTE (silbido en vivo)
// Cadena de escucha (AudioWorklet "escucha"):
//   micrófono -> ganancia -> |x| -> suavizado ataque/liberación -> envolvente e(t)
//   micrófono -> detector de altura (YIN simplificado) -> f(t) -> transposición
// Salidas: e(t) controla el volumen y el índice; f(t) controla la portadora.
// La toma se graba en estéreo: izquierda = micrófono, derecha = modelo.
// ¡Usa audífonos! Si el micrófono capta la salida, el sistema se realimenta.
// ============================================================================
const CODIGO_WORKLETS = `
class Escucha extends AudioWorkletProcessor {
  constructor() {
    super();
    this.p = { ganancia: 1, ataque: 10, liberacion: 200, umbral: -50, transp: -2, indice: 0.18, razon: 1 };
    this.port.onmessage = e => Object.assign(this.p, e.data);
    this.e = 0;                 // envolvente
    this.buf = new Float32Array(2048); this.pos = 0; this.cuenta = 0;
    this.f = 830; this.fObjetivo = 830; // altura detectada (Hz), suavizada
    this.tick = 0;
  }
  coef(ms) { return 1 - Math.exp(-1 / (ms / 1000 * sampleRate)); }
  // Detector de altura YIN simplificado: busca el retardo con menor diferencia normalizada.
  altura() {
    // Busca entre 400 y 4000 Hz (un silbido suele estar entre 500 y 3000 Hz).
    const N = 512, minL = Math.floor(sampleRate / 4000), maxL = Math.ceil(sampleRate / 400);
    const b = this.buf, largo = N + maxL + 2, x = this.lin || (this.lin = new Float32Array(largo));
    const ini = (this.pos - largo + b.length) % b.length;
    for (let i = 0; i < largo; i++) x[i] = b[(ini + i) % b.length];
    let acum = 0, mejor = -1;
    const d = this.d || (this.d = new Float32Array(maxL + 2));
    for (let L = 1; L <= maxL + 1; L++) {
      let s = 0;
      for (let i = 0; i < N; i++) { const z = x[i] - x[i + L]; s += z * z; }
      acum += s; d[L] = s * L / (acum || 1);
    }
    for (let L = minL; L <= maxL; L++) {
      if (d[L] < 0.15 && d[L] < d[L + 1]) { mejor = L; break; }
    }
    if (mejor < 0) return 0;
    const a = d[mejor - 1], bb = d[mejor], c = d[mejor + 1];
    const desp = (a - c) / (2 * (a - 2 * bb + c) || 1);
    return sampleRate / (mejor + desp);
  }
  process(inputs, outputs) {
    const ent = inputs[0][0], [o0, o1, o2] = outputs[0], p = this.p;
    const cA = this.coef(p.ataque), cL = this.coef(p.liberacion), cF = this.coef(15);
    const tr = Math.pow(2, p.transp / 12), umbral = Math.pow(10, p.umbral / 20);
    for (let i = 0; i < o0.length; i++) {
      const x = ent ? ent[i] * p.ganancia : 0;
      this.buf[this.pos] = x; this.pos = (this.pos + 1) % this.buf.length;
      const r = Math.abs(x);
      this.e += (r > this.e ? cA : cL) * (r - this.e);          // seguidor de envolvente
      if (++this.cuenta >= 512) {                                // cada 512 muestras (~11 ms): altura
        this.cuenta = 0;
        if (this.e > umbral) { const f = this.altura(); if (f > 0) this.fObjetivo = f; }
      }
      this.f += cF * (this.fObjetivo - this.f);
      const env = Math.min(1, this.e * Math.PI / 2);             // |sen| promedia 2/π: así un seno de amplitud 1 da 1
      const fc = this.f * tr;
      o0[i] = env; o1[i] = fc; o2[i] = p.indice * env * p.razon * fc;
    }
    if (++this.tick % 20 === 0) this.port.postMessage({ env: this.e * Math.PI / 2, f: this.f });
    return true;
  }
}
registerProcessor('escucha', Escucha);

class Grabadora extends AudioWorkletProcessor {
  constructor() { super(); this.on = false; this.port.onmessage = e => this.on = e.data; }
  process(inputs) {
    const ent = inputs[0];
    if (this.on && ent.length) {
      const L = ent[0].slice(), R = (ent[1] || ent[0]).slice();
      this.port.postMessage([L, R], [L.buffer, R.buffer]);
    }
    return true;
  }
}
registerProcessor('grabadora', Grabadora);
`;

const VIVO_PARAMS = [
  { id: 'ganancia', nombre: 'Ganancia de entrada', unidad: 'dB', min: -20, max: 40, paso: 1, def: 6 },
  { id: 'ataque', nombre: 'Ataque del seguidor', unidad: 'ms', min: 1, max: 100, paso: 1, def: 8 },
  { id: 'liberacion', nombre: 'Liberación del seguidor', unidad: 'ms', min: 10, max: 1000, paso: 5, def: 150 },
  { id: 'umbral', nombre: 'Umbral para detectar altura', unidad: 'dB', min: -80, max: -10, paso: 1, def: -45 },
  { id: 'transp', nombre: 'Transposición de la altura', unidad: 'semitonos', min: -36, max: 12, paso: 1, def: -2 }
];
const vivo = { activo: false, nodos: [], grabando: false, L: [], R: [], esc: null, rec: null };

function armarVivo() {
  const cont = document.getElementById('controles-vivo');
  VIVO_PARAMS.forEach(q => {
    const fila = document.createElement('div'); fila.className = 'fila';
    fila.innerHTML = `<label><b>${q.nombre}</b><span>${q.unidad}</span></label>
      <input type="range" min="${q.min}" max="${q.max}" step="${q.paso}" value="${q.def}">
      <output>${q.def}</output>`;
    cont.appendChild(fila);
    const r = fila.querySelector('input'), o = fila.querySelector('output');
    q.valor = q.def;
    r.oninput = () => { q.valor = +r.value; o.textContent = r.value; enviarVivo(); };
  });
  document.getElementById('vivo-on').onclick = iniciarVivo;
  document.getElementById('vivo-off').onclick = detenerVivo;
  document.getElementById('grabar').onclick = alternarGrabacion;
}
function enviarVivo() {
  if (!vivo.esc) return;
  const v = {}; VIVO_PARAMS.forEach(q => v[q.id] = q.valor);
  v.ganancia = Math.pow(10, v.ganancia / 20);
  v.indice = valores.indice; v.razon = valores.razon;
  vivo.esc.port.postMessage(v);
}

async function iniciarVivo() {
  const ctx = asegurarContexto(); detener(); detenerVivo();
  if (!vivo.cargado) {
    // El código de los worklets va dentro de esta página. Se carga como blob: (sitio web)
    // o, si la página se abrió como archivo local, como data: URL.
    try {
      await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([CODIGO_WORKLETS], { type: 'application/javascript' })));
    } catch (e) {
      await ctx.audioWorklet.addModule('data:application/javascript;charset=utf-8,' + encodeURIComponent(CODIGO_WORKLETS));
    }
    vivo.cargado = true;
  }
  const flujo = await navigator.mediaDevices.getUserMedia({ audio:
    { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  const mic = ctx.createMediaStreamSource(flujo);
  const esc = new AudioWorkletNode(ctx, 'escucha', { numberOfOutputs: 1, outputChannelCount: [3] });
  vivo.esc = esc; enviarVivo();
  esc.port.onmessage = e => {
    const { env, f } = e.data;
    document.getElementById('medidor').style.width = Math.min(100, env * 100) + '%';
    document.getElementById('altura-vivo').textContent =
      `${f.toFixed(0)} Hz detectados → ${(f * Math.pow(2, VIVO_PARAMS[4].valor / 12)).toFixed(0)} Hz en el modelo`;
  };
  mic.connect(esc);
  const sep = ctx.createChannelSplitter(3); esc.connect(sep);

  // Modelo FM controlado: las tres señales de control reemplazan a la partitura.
  const car = ctx.createOscillator(), mod = ctx.createOscillator();
  car.frequency.value = 0; mod.frequency.value = 0;
  sep.connect(car.frequency, 1);                                // fc = altura del silbido
  const razon = ctx.createGain(); razon.gain.value = valores.razon;
  sep.connect(razon, 1); razon.connect(mod.frequency);          // fm = razón · fc
  const desv = ctx.createGain(); desv.gain.value = 0;
  sep.connect(desv.gain, 2);                                    // desviación = I · e · fm
  mod.connect(desv).connect(car.frequency);
  const amp = ctx.createGain(); amp.gain.value = 0;
  sep.connect(amp.gain, 0);                                     // volumen = e(t)
  const pb = ctx.createBiquadFilter(); pb.type = 'lowpass'; pb.frequency.value = valores.corte;
  const seco = ctx.createGain(); seco.gain.value = 1 - valores.reverb / 100;
  const moj = ctx.createGain(); moj.gain.value = valores.reverb / 100;
  const conv = ctx.createConvolver(); conv.buffer = respuestaImpulso(ctx, 0.6);
  const master = ctx.createGain(); master.gain.value = 0.5;
  const pa = ctx.createBiquadFilter(); pa.type = 'highpass'; pa.frequency.value = 20;
  car.connect(amp).connect(pa).connect(pb); pb.connect(seco).connect(master);
  pb.connect(conv).connect(moj).connect(master);
  master.connect(analizador);                                   // a los audífonos

  // Grabadora estéreo: L = micrófono, R = modelo.
  const merge = ctx.createChannelMerger(2);
  mic.connect(merge, 0, 0); master.connect(merge, 0, 1);
  const rec = new AudioWorkletNode(ctx, 'grabadora', { channelCount: 2, channelCountMode: 'explicit' });
  rec.port.onmessage = e => { vivo.L.push(e.data[0]); vivo.R.push(e.data[1]); actualizarTiempo(); };
  const mudo = ctx.createGain(); mudo.gain.value = 0;
  merge.connect(rec).connect(mudo).connect(ctx.destination);
  vivo.rec = rec;

  car.start(); mod.start();
  vivo.nodos = [car, mod]; vivo.flujo = flujo; vivo.mic = mic; vivo.activo = true;
  document.getElementById('estado-vivo').textContent = 'Escuchando. Silba frente al micrófono (con audífonos).';
}
function detenerVivo() {
  if (!vivo.activo) return;
  if (vivo.grabando) alternarGrabacion();
  vivo.nodos.forEach(n => { try { n.stop(); } catch (e) {} });
  vivo.flujo.getTracks().forEach(t => t.stop());
  vivo.mic.disconnect(); vivo.esc.disconnect(); vivo.rec.disconnect();
  vivo.activo = false; vivo.esc = null;
  document.getElementById('estado-vivo').textContent = 'Detenido.';
}
function alternarGrabacion() {
  if (!vivo.activo) { alert('Primero activa el micrófono.'); return; }
  const b = document.getElementById('grabar');
  if (!vivo.grabando) {
    vivo.L = []; vivo.R = []; vivo.grabando = true; vivo.rec.port.postMessage(true);
    b.textContent = 'Detener y descargar la toma';
  } else {
    vivo.grabando = false; vivo.rec.port.postMessage(false);
    b.textContent = 'Grabar toma';
    const unir = partes => { const n = partes.reduce((s, x) => s + x.length, 0), o = new Float32Array(n);
      let k = 0; partes.forEach(x => { o.set(x, k); k += x.length; }); return o; };
    descargar(aWav([unir(vivo.L), unir(vivo.R)], ctxVivo.sampleRate), `parte4_silbido_L_modelo_R_${Date.now()}.wav`);
  }
}
function actualizarTiempo() {
  const s = vivo.L.length * 128 / ctxVivo.sampleRate;
  document.getElementById('tiempo-toma').textContent = `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
}
