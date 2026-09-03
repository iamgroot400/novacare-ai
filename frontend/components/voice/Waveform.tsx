"use client";

import { useEffect, useRef } from "react";

export function Waveform({ stream, active }: { stream: MediaStream | null; active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let audioCtx: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let data: Uint8Array | null = null;

    if (stream) {
      audioCtx = new AudioContext();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      audioCtx.createMediaStreamSource(stream).connect(analyser);
      data = new Uint8Array(analyser.frequencyBinCount);
    }

    const bars = 48;
    const draw = () => {
      const w = (canvas.width = canvas.clientWidth * devicePixelRatio);
      const h = (canvas.height = canvas.clientHeight * devicePixelRatio);
      ctx.clearRect(0, 0, w, h);
      if (analyser && data) analyser.getByteFrequencyData(data);
      const bw = w / bars;
      for (let i = 0; i < bars; i++) {
        const v = data ? data[Math.floor((i / bars) * data.length)] / 255 : 0;
        const idle = 0.08 + 0.06 * Math.sin(Date.now() / 240 + i / 2);
        const amp = active ? Math.max(v, idle) : idle;
        const bh = amp * h * 0.9;
        const grad = ctx.createLinearGradient(0, h / 2 - bh / 2, 0, h / 2 + bh / 2);
        grad.addColorStop(0, "#5b8cff");
        grad.addColorStop(1, "#1f42f5");
        ctx.fillStyle = grad;
        const x = i * bw + bw * 0.2;
        ctx.beginPath();
        ctx.roundRect(x, h / 2 - bh / 2, bw * 0.6, bh, bw * 0.3);
        ctx.fill();
      }
      rafRef.current = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      audioCtx?.close();
    };
  }, [stream, active]);

  return <canvas ref={canvasRef} className="h-24 w-full" />;
}
