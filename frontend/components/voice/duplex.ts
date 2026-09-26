// Full-duplex call over a WebSocket (works on any network: it's just HTTPS, no UDP/TURN).
//   up:   raw 16 kHz mono PCM16 from the mic, continuously; the server's VAD decides turns
//   down: 0x01 + 24 kHz mono PCM16 = bot audio to play; 0x02 = caller barged in, stop playback

const MIC_WORKLET = `
class Mic16k extends AudioWorkletProcessor {
  constructor() { super(); this.step = sampleRate / 16000; this.t = 0; this.sum = 0; this.n = 0;
    this.out = new Int16Array(320); this.i = 0; }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let k = 0; k < ch.length; k++) {
      this.sum += ch[k]; this.n++; this.t += 1;
      if (this.t >= this.step) {            // average each window, then decimate to 16 kHz
        this.t -= this.step;
        const v = Math.max(-1, Math.min(1, this.sum / this.n));
        this.out[this.i++] = v * 32767; this.sum = 0; this.n = 0;
        if (this.i === this.out.length) {   // 20 ms per message
          this.port.postMessage(this.out.buffer, [this.out.buffer]);
          this.out = new Int16Array(320); this.i = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor("mic-16k", Mic16k);
`;

export interface DuplexCall {
  stop: () => void;
}

export async function startDuplexCall(opts: {
  url: string;
  stream: MediaStream;
  onBotTalking: (talking: boolean) => void;
  onClosed: () => void;
}): Promise<DuplexCall> {
  const ctx = new AudioContext();
  const moduleUrl = URL.createObjectURL(new Blob([MIC_WORKLET], { type: "application/javascript" }));
  await ctx.audioWorklet.addModule(moduleUrl);
  URL.revokeObjectURL(moduleUrl);

  const mic = new AudioWorkletNode(ctx, "mic-16k");
  const sink = ctx.createGain();
  sink.gain.value = 0; // keep the worklet pulled by the graph without playing the mic back
  ctx.createMediaStreamSource(opts.stream).connect(mic).connect(sink).connect(ctx.destination);

  const ws = new WebSocket(opts.url);
  ws.binaryType = "arraybuffer";
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("voice connection timed out")), 8000);
    ws.onopen = () => {
      clearTimeout(timer);
      resolve();
    };
    ws.onerror = () => {
      clearTimeout(timer);
      reject(new Error("voice connection failed"));
    };
  });

  mic.port.onmessage = (e) => {
    if (ws.readyState === WebSocket.OPEN) ws.send(e.data as ArrayBuffer);
  };

  // Bot audio is scheduled back to back; a barge-in (0x02) stops everything queued.
  const playing = new Set<AudioBufferSourceNode>();
  let playAt = 0;
  const stopPlayback = () => {
    playing.forEach((s) => s.stop());
    playing.clear();
    playAt = 0;
    opts.onBotTalking(false);
  };
  ws.onmessage = (e) => {
    const bytes = new Uint8Array(e.data as ArrayBuffer);
    if (bytes[0] === 2) return stopPlayback();
    if (bytes[0] !== 1 || bytes.length < 3) return;
    const pcm = new Int16Array((e.data as ArrayBuffer).slice(1));
    const buf = ctx.createBuffer(1, pcm.length, 24000);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);
    playAt = Math.max(playAt, ctx.currentTime + 0.03);
    src.start(playAt);
    playAt += buf.duration;
    playing.add(src);
    opts.onBotTalking(true);
    src.onended = () => {
      playing.delete(src);
      if (!playing.size) opts.onBotTalking(false);
    };
  };
  ws.onclose = () => {
    stopPlayback();
    opts.onClosed();
  };

  return {
    stop: () => {
      ws.onclose = null;
      ws.close();
      stopPlayback();
      void ctx.close();
    },
  };
}
