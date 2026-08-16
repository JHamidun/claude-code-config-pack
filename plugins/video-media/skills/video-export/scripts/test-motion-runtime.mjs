/**
 * Проверка слоя выполнения анимаций.
 *
 * Сцены отлажены покадрово, поэтому расхождение в кривой или на краю диапазона сдвинет
 * то, что подбиралось часами. Проверяем не «вызывается ли функция», а совпадают ли
 * числа с известными значениями.
 *
 *   node test-motion-runtime.mjs
 */
import {
  interpolate, interpolateColors, Easing, spring,
  useCurrentFrame, setTime, configure, useVideoConfig, random, ABSOLUTE_FILL_STYLE,
} from './motion-runtime.mjs';

let pass = 0, fail = 0;
const close = (a, b, eps = 1e-3) => Math.abs(a - b) < eps;

function check(name, got, want, eps) {
  const ok = typeof want === 'number' ? close(got, want, eps) : got === want;
  if (ok) { pass++; console.log(`  ок    ${name}`); }
  else { fail++; console.log(`  МИМО  ${name}: получено ${got}, ожидалось ${want}`); }
}

console.log('--- интерполяция ---');
check('середина отрезка', interpolate(5, [0, 10], [0, 100]), 50);
check('левый край зажат', interpolate(-5, [0, 10], [0, 100]), 0);
check('правый край зажат', interpolate(15, [0, 10], [0, 100]), 100);
check('без зажима слева', interpolate(-5, [0, 10], [0, 100], { extrapolateLeft: 'extend' }), -50);
check('обратный выход', interpolate(5, [0, 10], [100, 0]), 50);
check('многоточечный: первый отрезок', interpolate(2.5, [0, 5, 10], [0, 50, 0]), 25);
check('многоточечный: второй отрезок', interpolate(7.5, [0, 5, 10], [0, 50, 0]), 25);
check('вырожденный отрезок', interpolate(5, [5, 5], [10, 20]), 10);

console.log('\n--- кривые ---');
check('линейная в середине', Easing.linear(0.5), 0.5);
check('квадратичная в середине', Easing.quad(0.5), 0.25);
check('кубическая в середине', Easing.cubic(0.5), 0.125);
check('развёрнутая кубическая', Easing.out(Easing.cubic)(0.5), 0.875);
check('кривая: начало', Easing.bezier(0.25, 0.1, 0.25, 1)(0), 0);
check('кривая: конец', Easing.bezier(0.25, 0.1, 0.25, 1)(1), 1);
// Стандартная кривая ease в середине даёт ≈0.8024 — известное табличное значение
check('кривая ease в середине', Easing.bezier(0.25, 0.1, 0.25, 1)(0.5), 0.8024, 5e-3);
// Прямая, заданная как безье, обязана совпасть с линейной
check('безье-прямая = линейная', Easing.bezier(0, 0, 1, 1)(0.37), 0.37, 5e-3);
// У кривой с перелётом он в НАЧАЛЕ: значение сначала уходит ниже нуля (замах),
// а выше единицы выходит уже развёрнутая форма — на выходе, а не на входе.
check('замах уходит ниже нуля', Easing.back()(0.15) < 0, true);
check('развёрнутая перелетает цель', Easing.out(Easing.back())(0.85) > 1, true);
check('поли степени 5', Easing.poly(5)(0.5), 0.03125);

console.log('\n--- интерполяция с кривой ---');
check('квадратичная в интерполяции',
      interpolate(0.5, [0, 1], [0, 100], { easing: Easing.quad }), 25);

console.log('\n--- время ---');
configure({ fps: 30 });
setTime(0);
check('нулевой кадр', useCurrentFrame(), 0);
setTime(1);
check('через секунду 30 кадров', useCurrentFrame(), 30);
setTime(2.5);
check('дробное время', useCurrentFrame(), 75);
check('параметры ролика', useVideoConfig().fps, 30);

console.log('\n--- пружина ---');
check('пружина в нуле', spring({ frame: 0, fps: 30 }), 0, 1e-6);
check('пружина сошлась к цели', close(spring({ frame: 90, fps: 30 }), 1, 0.02), true);
const mid = spring({ frame: 8, fps: 30 });
check('пружина в движении', mid > 0 && mid < 1.6, true);
check('зажатый перелёт',
      spring({ frame: 12, fps: 30, config: { overshootClamping: true } }) <= 1, true);

console.log('\n--- цвет ---');
check('цвет: середина', interpolateColors(0.5, [0, 1], ['#000000', '#ffffff']),
      'rgba(128, 128, 128, 1.000)');
check('цвет: край', interpolateColors(0, [0, 1], ['#ff0000', '#00ff00']),
      'rgba(255, 0, 0, 1.000)');

console.log('\n--- прочее ---');
check('слой на весь экран', ABSOLUTE_FILL_STYLE.position, 'absolute');
check('шум повторяем', random('a') === random('a'), true);
check('шум различает семена', random('a') !== random('b'), true);
check('шум в пределах нуля-единицы', random('x') >= 0 && random('x') < 1, true);

console.log(`\n  прошло ${pass}, промахов ${fail}`);
process.exit(fail ? 1 : 0);
