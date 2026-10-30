// ============================================================================
// Modelo B — SÍNTESIS FM (modulación de frecuencia)
// Una moduladora (fm = razón·fc) hace oscilar la frecuencia de una portadora
// (fc = f0). Los parciales aparecen en fc ± k·fm con amplitudes J_k(I).
// El índice I sigue a la envolvente: más fuerte = más brillante.
// Después: pasa altos de 20 Hz (quita la continua), filtro pasa bajos y reverberación por convolución (con una
// respuesta al impulso sintética, nunca la grabación).
// ============================================================================
const MODELO = {
  nombre: 'Modelo B · Síntesis FM',
  archivo: 'fm',
  parametros: [
    { id: 'f0', nombre: 'f0 base', unidad: 'Hz', min: 100, max: 3000, paso: 1, def: 830,
      efecto: 'Altura de la meseta (frecuencia de la portadora); el contorno se transpone con ella.' },
    { id: 'contorno', nombre: 'Contorno de altura', unidad: '%', min: 0, max: 300, paso: 1, def: 100,
      efecto: 'Cuánto del deslizamiento medido se aplica: 0 = altura fija.' },
    { id: 'estirar', nombre: 'Estiramiento', unidad: '×', min: 0.25, max: 30, paso: 0.05, def: 1,
      efecto: 'Duración del gesto; 1 = 1,302 s como el original.' },
    { id: 'pulsos', nombre: 'Pulsos', unidad: '%', min: 0, max: 100, paso: 1, def: 70,
      efecto: 'Profundidad de los pulsos de volumen entre 0,09 y 0,45 s (modulación de amplitud).' },
    { id: 'tasa', nombre: 'Tasa de pulsos', unidad: '×', min: 0.1, max: 8, paso: 0.05, def: 1,
      efecto: 'Multiplica la tasa medida (75 → 27 pulsos por segundo).' },
    { id: 'razon', nombre: 'Razón fm/fc', unidad: 'proporción', min: 0.1, max: 8, paso: 0.01, def: 1,
      efecto: 'Entera: espectro armónico. No entera: parciales inarmónicos (metálico).' },
    { id: 'indice', nombre: 'Índice máximo', unidad: 'I', min: 0, max: 12, paso: 0.01, def: 0.18,
      efecto: 'Cantidad y peso de los parciales; se alcanza en el punto más fuerte de la envolvente.' },
    { id: 'corte', nombre: 'Corte pasa bajos', unidad: 'Hz', min: 200, max: 20000, paso: 10, def: 12000,
      efecto: 'Atenúa los parciales sobre esta frecuencia (filtro biquad, Q 0,707).' },
    { id: 'reverb', nombre: 'Reverberación', unidad: '%', min: 0, max: 100, paso: 1, def: 8,
      efecto: 'Mezcla de la convolución con una respuesta al impulso sintética de 0,6 s.' }
  ],

  construir(ctx, p, t0, salida) {
    const c = curvas(p), nodos = [], fin = t0 + c.D + 0.05;

    // Portadora: su frecuencia base sigue f0(t)...
    const car = ctx.createOscillator();
    car.frequency.setValueCurveAtTime(c.f0, t0, c.D);
    // ...y la moduladora le suma una desviación de I(t)·fm(t) Hz.
    const mod = ctx.createOscillator();
    mod.frequency.setValueCurveAtTime(c.f0.map(f => f * p.razon), t0, c.D);
    const desv = ctx.createGain(); desv.gain.value = 0;
    desv.gain.setValueCurveAtTime(c.f0.map((f, i) => p.indice * c.amp[i] * p.razon * f), t0, c.D);
    mod.connect(desv).connect(car.frequency);

    // Envolvente -> pulsos -> pasa bajos -> (seco + convolución) -> salida
    const env = ctx.createGain(); env.gain.value = 0;
    env.gain.setValueCurveAtTime(c.amp, t0, c.D);
    const trem = crearPulsos(ctx, c, t0, nodos);
    const pb = ctx.createBiquadFilter(); pb.type = 'lowpass';
    pb.frequency.value = Math.min(p.corte, ctx.sampleRate / 2 - 100); pb.Q.value = 0.707;
    const seco = ctx.createGain(); seco.gain.value = 1 - p.reverb / 100;
    const mojado = ctx.createGain(); mojado.gain.value = p.reverb / 100;
    const conv = ctx.createConvolver(); conv.buffer = respuestaImpulso(ctx, 0.6);
    const master = ctx.createGain(); master.gain.value = 0.5;
    // Con razón 1 aparece una componente en fc − fm = 0 Hz (continua); un pasa altos de 20 Hz la quita.
    const pa = ctx.createBiquadFilter(); pa.type = 'highpass'; pa.frequency.value = 20; pa.Q.value = 0.707;
    car.connect(env).connect(trem).connect(pa).connect(pb);
    pb.connect(seco).connect(master);
    pb.connect(conv).connect(mojado).connect(master);
    master.connect(salida);

    [car, mod].forEach(o => { o.start(t0); o.stop(fin); nodos.push(o); });
    return nodos;
  }
};

// Respuesta al impulso sintética: ruido con caída exponencial (RT60 = segundos).
function respuestaImpulso(ctx, rt60) {
  const n = Math.ceil(rt60 * ctx.sampleRate), b = ctx.createBuffer(1, n, ctx.sampleRate);
  const d = b.getChannelData(0), r = rng(777), tau = rt60 / 6.91;
  for (let i = 0; i < n; i++) d[i] = r() * Math.exp(-(i / ctx.sampleRate) / tau);
  return b;
}
