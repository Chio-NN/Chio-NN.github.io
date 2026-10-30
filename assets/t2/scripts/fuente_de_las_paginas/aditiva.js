// ============================================================================
// Modelo A — SÍNTESIS ADITIVA
// Un oscilador seno por armónico (k·f0), cada uno con su propio volumen.
// Encima: la envolvente medida, los pulsos (AM) y un ruido filtrado en
// pasa banda (el filtro digital que exige la tarea).
// ============================================================================
const MODELO = {
  nombre: 'Modelo A · Síntesis aditiva',
  archivo: 'aditiva',
  parametros: [
    { id: 'f0', nombre: 'f0 base', unidad: 'Hz', min: 100, max: 3000, paso: 1, def: 830,
      efecto: 'Altura de la meseta; todo el contorno se transpone con ella.' },
    { id: 'contorno', nombre: 'Contorno de altura', unidad: '%', min: 0, max: 300, paso: 1, def: 100,
      efecto: 'Cuánto del deslizamiento medido se aplica: 0 = altura fija, 200 = el doble de semitonos.' },
    { id: 'estirar', nombre: 'Estiramiento', unidad: '×', min: 0.25, max: 30, paso: 0.05, def: 1,
      efecto: 'Duración del gesto; 1 = 1,302 s como el original.' },
    { id: 'pulsos', nombre: 'Pulsos', unidad: '%', min: 0, max: 100, paso: 1, def: 70,
      efecto: 'Profundidad de los pulsos de volumen entre 0,09 y 0,45 s (modulación de amplitud).' },
    { id: 'tasa', nombre: 'Tasa de pulsos', unidad: '×', min: 0.1, max: 8, paso: 0.05, def: 1,
      efecto: 'Multiplica la tasa medida (75 → 27 pulsos por segundo).' },
    { id: 'armonicos', nombre: 'Armónicos', unidad: 'cantidad', min: 1, max: 16, paso: 1, def: 10,
      efecto: 'Cuántos senos se suman (k = 1 … N). 1 = seno puro.' },
    { id: 'brillo', nombre: 'Brillo', unidad: 'dB', min: -80, max: 0, paso: 1, def: -36,
      efecto: 'Nivel del 3.er armónico respecto de la fundamental; los siguientes bajan 1,5 dB cada uno.' },
    { id: 'oscurecer', nombre: 'Oscurecimiento', unidad: 'dB', min: -20, max: 40, paso: 1, def: 12,
      efecto: 'Cuánto pierden los armónicos 3 y superiores entre el inicio y el final.' },
    { id: 'ruido', nombre: 'Ruido', unidad: 'dB', min: -90, max: -10, paso: 1, def: -39,
      efecto: 'Nivel del ruido filtrado en pasa banda (5 kHz, Q 0,7) respecto de la fundamental.' }
  ],

  // Construye el grafo de nodos. Sirve igual para tiempo real y para exportar.
  construir(ctx, p, t0, salida) {
    const c = curvas(p), nodos = [], fin = t0 + c.D + 0.05;
    const nyq = ctx.sampleRate / 2;

    // Envolvente de amplitud -> pulsos -> salida (con margen de -6 dB)
    const env = ctx.createGain(); env.gain.value = 0;
    env.gain.setValueCurveAtTime(c.amp, t0, c.D);
    const trem = crearPulsos(ctx, c, t0, nodos);
    const master = ctx.createGain(); master.gain.value = 0.5;
    env.connect(trem).connect(master).connect(salida);

    // Banco de osciladores: el armónico k sigue la curva k·f0(t).
    const H2 = Math.pow(10, -26 / 20); // 2.º armónico fijo: promedio medido (−26 dB)
    for (let k = 1; k <= p.armonicos; k++) {
      const osc = ctx.createOscillator();
      const fk = c.f0.map(f => Math.min(k * f, nyq * 0.98));
      osc.frequency.setValueCurveAtTime(fk, t0, c.D);
      const g = ctx.createGain(); g.gain.value = 0;
      const nivel = new Float32Array(c.n);
      for (let i = 0; i < c.n; i++) {
        let a;
        if (k === 1) a = 1;
        else if (k === 2) a = H2;
        else {
          // Nivel en dB: brillo, menos 1,5 dB por armónico, menos el oscurecimiento en el tiempo
          const u = i / (c.n - 1);
          const db = p.brillo - 1.5 * (k - 3) + p.oscurecer * (0.5 - u);
          a = Math.pow(10, db / 20);
        }
        nivel[i] = (k * c.f0[i] < nyq * 0.95) ? a : 0; // evita el aliasing
      }
      g.gain.setValueCurveAtTime(nivel, t0, c.D);
      osc.connect(g).connect(env);
      osc.start(t0); osc.stop(fin);
      nodos.push(osc);
    }

    // Ruido blanco -> filtro pasa banda -> mismo camino de envolvente.
    // Calibración: el ruido filtrado (RMS ≈ 0,31) queda "ruido" dB bajo la fundamental (RMS 0,707).
    const ruido = ctx.createBufferSource();
    ruido.buffer = bufferRuido(ctx, c.D + 0.1, 1234);
    const pb = ctx.createBiquadFilter(); pb.type = 'bandpass'; pb.frequency.value = 5000; pb.Q.value = 0.7;
    const gr = ctx.createGain(); gr.gain.value = Math.pow(10, p.ruido / 20) * (0.707 / 0.31);
    ruido.connect(pb).connect(gr).connect(env);
    ruido.start(t0); ruido.stop(fin);
    nodos.push(ruido);
    return nodos;
  }
};
