import fs from 'node:fs/promises';
import path from 'node:path';
import { createCanvas, loadImage } from 'canvas';   // npm i canvas

const dir = process.argv[2] || 'moodboard/refs';
const k = +(process.argv[3] || 5);

for (const f of await fs.readdir(dir)) {
  if (!/\.(jpg|jpeg|png|webp)$/i.test(f)) continue;
  const img = await loadImage(path.join(dir, f));
  const w = 80, h = Math.round(80 * img.height / img.width);
  const c = createCanvas(w, h); const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0, w, h);
  const data = ctx.getImageData(0, 0, w, h).data;

  // K-means crude
  const points = [];
  for (let i = 0; i < data.length; i += 4) {
    if (data[i+3] < 100) continue;
    points.push([data[i], data[i+1], data[i+2]]);
  }
  let centers = Array.from({length: k}, () => points[Math.floor(Math.random()*points.length)]);
  for (let iter = 0; iter < 8; iter++) {
    const buckets = Array.from({length: k}, () => []);
    for (const p of points) {
      let best = 0, bd = Infinity;
      for (let i = 0; i < k; i++) {
        const d = (p[0]-centers[i][0])**2 + (p[1]-centers[i][1])**2 + (p[2]-centers[i][2])**2;
        if (d < bd) { bd = d; best = i; }
      }
      buckets[best].push(p);
    }
    centers = buckets.map(b => {
      if (!b.length) return centers[0];
      const sum = b.reduce((a,x) => [a[0]+x[0], a[1]+x[1], a[2]+x[2]], [0,0,0]);
      return [sum[0]/b.length|0, sum[1]/b.length|0, sum[2]/b.length|0];
    });
  }
  const hex = centers.map(c => '#' + c.map(n => n.toString(16).padStart(2,'0')).join(''));
  console.log(f, hex);
}
