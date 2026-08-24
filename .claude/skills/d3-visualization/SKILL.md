---
name: d3-visualization
description: "Интерактивные графики и визуализации данных на D3.js. Триггеры: «построй чарт», «график данных», «data visualization»."
---

# D3.js Visualization Skill

## Overview

Создание интерактивных визуализаций данных с D3.js: графики, диаграммы, карты.

## When to Use

- Интерактивные графики
- Кастомные визуализации
- Data storytelling
- Dashboards
- Анимированные диаграммы

## D3 Basics

### Setup

**Сначала реши, где страница будет открываться — от этого зависит способ подключения.**

| Где живёт страница | CDN-тег | Что делать |
|---|---|---|
| Артефакт claude.ai | **не грузится** (строгий CSP на внешние хосты) | тело d3 инлайном в `<script>` |
| Файл на диске / свой сервер | работает, пока есть интернет | CDN или `npm install d3` |
| Файл, отправленный человеку | работает только у него в онлайне | тело d3 инлайном |

Отказ здесь молчаливый: CSP блокирует запрос, `d3` остаётся `undefined`, скрипт
падает первой же строкой — и человек видит **пустую белую страницу**, без единой
ошибки на экране. Поэтому под артефакт — только инлайн.

```html
<!-- 1. Диск или свой сервер: CDN -->
<script src="https://d3js.org/d3.v7.min.js"></script>

<!-- Или сборка: npm install d3 -->

<!-- 2. Артефакт claude.ai / офлайн: тело библиотеки внутрь файла (~280 КБ) -->
<script>
/* ...сюда содержимое d3.v7.min.js целиком... */
</script>
```

Скачать тело для вставки:

```bash
curl -sL https://d3js.org/d3.v7.min.js -o d3.v7.min.js   # затем вставить внутрь <script>
```

**Громкая проверка вместо белого экрана.** Первой строкой своего скрипта — гард,
который превращает «ничего не нарисовалось» в названную ошибку:

```html
<div id="chart"></div>
<script>
if (typeof d3 === 'undefined') {
  document.getElementById('chart').innerHTML =
    '<p style="padding:1rem;border:2px solid #c00;color:#c00;font:14px system-ui">' +
    'D3 не загрузился. На артефактах claude.ai внешние скрипты блокирует CSP — ' +
    'вставь тело d3.v7.min.js прямо в &lt;script&gt;.</p>';
  throw new Error('d3 is not defined: CDN blocked or offline');
}
// ...дальше обычный код графика
</script>
```

Проверить, что файл самодостаточен (пусто = ни одной внешней загрузки):

```bash
grep -nE '<(script|link)[^>]+(src|href)="https?://' chart.html
```

Полный разбор самодостаточного файла — `references/selfcontained-dashboard.md`.

### Core Concepts

```javascript
// Selection
d3.select("#chart")       // Single element
d3.selectAll(".bar")      // Multiple elements

// Data binding
const data = [10, 20, 30, 40, 50];

d3.select("#chart")
  .selectAll("rect")
  .data(data)
  .join("rect")
  .attr("height", d => d)
  .attr("width", 20);

// Scales
const xScale = d3.scaleLinear()
  .domain([0, 100])    // Input range
  .range([0, 500]);    // Output range

const colorScale = d3.scaleOrdinal()
  .domain(["A", "B", "C"])
  .range(["red", "green", "blue"]);
```

## Chart Templates

### Bar Chart

```javascript
function barChart(data, selector) {
  const margin = { top: 20, right: 20, bottom: 30, left: 40 };
  const width = 600 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;

  // Clear previous
  d3.select(selector).html("");

  // SVG container
  const svg = d3.select(selector)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Scales
  const x = d3.scaleBand()
    .domain(data.map(d => d.label))
    .range([0, width])
    .padding(0.2);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value)])
    .nice()
    .range([height, 0]);

  // Axes
  svg.append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(x));

  svg.append("g")
    .call(d3.axisLeft(y));

  // Bars
  svg.selectAll(".bar")
    .data(data)
    .join("rect")
    .attr("class", "bar")
    .attr("x", d => x(d.label))
    .attr("y", d => y(d.value))
    .attr("width", x.bandwidth())
    .attr("height", d => height - y(d.value))
    .attr("fill", "steelblue")
    .on("mouseover", function() {
      d3.select(this).attr("fill", "orange");
    })
    .on("mouseout", function() {
      d3.select(this).attr("fill", "steelblue");
    });
}

// Usage
const data = [
  { label: "A", value: 30 },
  { label: "B", value: 80 },
  { label: "C", value: 45 },
  { label: "D", value: 60 },
  { label: "E", value: 20 }
];

barChart(data, "#chart");
```

### Line Chart

```javascript
function lineChart(data, selector) {
  const margin = { top: 20, right: 30, bottom: 30, left: 50 };
  const width = 600 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;

  d3.select(selector).html("");

  const svg = d3.select(selector)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Parse dates if needed
  const parseDate = d3.timeParse("%Y-%m-%d");
  data.forEach(d => {
    d.date = parseDate(d.date);
  });

  // Scales
  const x = d3.scaleTime()
    .domain(d3.extent(data, d => d.date))
    .range([0, width]);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value)])
    .nice()
    .range([height, 0]);

  // Line generator
  const line = d3.line()
    .x(d => x(d.date))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX);

  // Axes
  svg.append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(6));

  svg.append("g")
    .call(d3.axisLeft(y));

  // Line path
  svg.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 2)
    .attr("d", line);

  // Dots
  svg.selectAll(".dot")
    .data(data)
    .join("circle")
    .attr("class", "dot")
    .attr("cx", d => x(d.date))
    .attr("cy", d => y(d.value))
    .attr("r", 4)
    .attr("fill", "steelblue");
}
```

### Pie Chart

```javascript
function pieChart(data, selector) {
  const width = 400;
  const height = 400;
  const radius = Math.min(width, height) / 2;

  d3.select(selector).html("");

  const svg = d3.select(selector)
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", `translate(${width/2},${height/2})`);

  // Color scale
  const color = d3.scaleOrdinal()
    .domain(data.map(d => d.label))
    .range(d3.schemeCategory10);

  // Pie generator
  const pie = d3.pie()
    .value(d => d.value)
    .sort(null);

  // Arc generator
  const arc = d3.arc()
    .innerRadius(0)
    .outerRadius(radius - 10);

  const arcHover = d3.arc()
    .innerRadius(0)
    .outerRadius(radius);

  // Draw slices
  svg.selectAll("path")
    .data(pie(data))
    .join("path")
    .attr("d", arc)
    .attr("fill", d => color(d.data.label))
    .attr("stroke", "white")
    .attr("stroke-width", 2)
    .on("mouseover", function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .attr("d", arcHover);
    })
    .on("mouseout", function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .attr("d", arc);
    });

  // Labels
  svg.selectAll("text")
    .data(pie(data))
    .join("text")
    .attr("transform", d => `translate(${arc.centroid(d)})`)
    .attr("text-anchor", "middle")
    .text(d => d.data.label)
    .style("font-size", "12px")
    .style("fill", "white");
}
```

### Donut Chart

```javascript
function donutChart(data, selector) {
  const width = 400;
  const height = 400;
  const radius = Math.min(width, height) / 2;
  const innerRadius = radius * 0.6;  // Donut hole

  // ... same as pie but with:
  const arc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(radius - 10);

  // Center text
  svg.append("text")
    .attr("text-anchor", "middle")
    .attr("dy", "0.35em")
    .style("font-size", "24px")
    .text(d3.sum(data, d => d.value));
}
```

## Interactive Features

### Tooltip

```javascript
// Create tooltip div
const tooltip = d3.select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("position", "absolute")
  .style("visibility", "hidden")
  .style("background", "rgba(0,0,0,0.8)")
  .style("color", "white")
  .style("padding", "8px")
  .style("border-radius", "4px");

// Add to elements
svg.selectAll("rect")
  .on("mouseover", function(event, d) {
    tooltip
      .style("visibility", "visible")
      .html(`<strong>${d.label}</strong><br>Value: ${d.value}`);
  })
  .on("mousemove", function(event) {
    tooltip
      .style("top", (event.pageY - 10) + "px")
      .style("left", (event.pageX + 10) + "px");
  })
  .on("mouseout", function() {
    tooltip.style("visibility", "hidden");
  });
```

### Zoom & Pan

```javascript
const zoom = d3.zoom()
  .scaleExtent([0.5, 5])
  .on("zoom", (event) => {
    svg.attr("transform", event.transform);
  });

d3.select("svg").call(zoom);
```

### Transitions

```javascript
// Animate bars
svg.selectAll(".bar")
  .data(newData)
  .transition()
  .duration(750)
  .attr("y", d => y(d.value))
  .attr("height", d => height - y(d.value));

// Animate line
path
  .transition()
  .duration(1000)
  .attrTween("stroke-dasharray", function() {
    const length = this.getTotalLength();
    return d3.interpolate(`0,${length}`, `${length},${length}`);
  });
```

## Responsive Charts

```javascript
function responsiveChart(selector) {
  const container = d3.select(selector);

  function render() {
    const width = container.node().getBoundingClientRect().width;
    const height = width * 0.6;

    container.html("");

    const svg = container
      .append("svg")
      .attr("width", width)
      .attr("height", height);

    // ... draw chart with calculated dimensions
  }

  render();

  // Resize handler
  d3.select(window).on("resize", () => {
    render();
  });
}
```

## Common Scales

```javascript
// Linear (continuous numbers)
d3.scaleLinear().domain([0, 100]).range([0, 500])

// Time
d3.scaleTime().domain([startDate, endDate]).range([0, width])

// Ordinal (categories)
d3.scaleOrdinal().domain(["A", "B", "C"]).range(["red", "green", "blue"])

// Band (for bar charts)
d3.scaleBand().domain(categories).range([0, width]).padding(0.1)

// Log
d3.scaleLog().domain([1, 1000]).range([0, 500])

// Sqrt
d3.scaleSqrt().domain([0, 100]).range([0, 20])  // For bubble sizes
```

## Color Schemes

```javascript
// Built-in schemes
d3.schemeCategory10      // 10 colors
d3.schemeTableau10       // Tableau colors
d3.schemePaired          // 12 paired colors
d3.schemeSet3            // 12 pastel colors

// Sequential
d3.interpolateBlues      // Light to dark blue
d3.interpolateViridis    // Purple-yellow
d3.interpolateRdYlGn     // Red-yellow-green

// Usage with scale
const colorScale = d3.scaleSequential()
  .domain([0, 100])
  .interpolator(d3.interpolateViridis);
```

## Data Transformations

```javascript
// Group data
const grouped = d3.group(data, d => d.category);

// Rollup (aggregate)
const totals = d3.rollup(data,
  v => d3.sum(v, d => d.value),
  d => d.category
);

// Stack (for stacked charts)
const stack = d3.stack()
  .keys(["A", "B", "C"]);

const stackedData = stack(data);

// Bin (histogram)
const bins = d3.bin()
  .domain([0, 100])
  .thresholds(10)
  (data);
```

## Дашборд одним файлом

Когда нужен не график, а **срез с фильтрами**, который открывается двойным кликом и уезжает
человеку файлом — `references/selfcontained-dashboard.md`: каркас с единой точкой фильтрации,
KPI-карточки (с `higherIsBetter`, чтобы рост оттока не подсвечивался зелёным), сортируемая
таблица с `localeCompare('ru')`, пороги по объёму данных и предагрегация, таблица выбора типа
графика и правила честной подачи. Там же — требование самодостаточности: CDN под CSP артефактов
не грузится, всё инлайном.

## Tips

1. **Margins convention** - всегда используй margin pattern
2. **Data join** - понимай enter/update/exit
3. **Transitions** - анимируй изменения
4. **Responsive** - используй viewBox или resize handlers
5. **Tooltips** - добавляй интерактивность
6. **Accessibility** - добавляй ARIA labels
7. **Performance** - используй Canvas для больших данных
