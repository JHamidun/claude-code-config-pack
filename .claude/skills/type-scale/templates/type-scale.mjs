const base  = +(process.argv[2] || 16);
const ratio = +(process.argv[3] || 1.25);
const names = ['xs','sm','base','lg','xl','2xl','3xl','4xl','5xl','6xl'];
const offset = -2;

console.log(':root {');
names.forEach((n, i) => {
  const px = (base * Math.pow(ratio, i + offset)).toFixed(0);
  console.log(`  --text-${n}: ${px}px;`);
});
console.log('}');
