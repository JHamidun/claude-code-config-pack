// Wordstat real-data snippet — paste into browser_evaluate on a LOGGED-IN wordstat.yandex.ru page.
// Возвращает {фраза: показов/мес} + расширения. CSRF не нужен, куки сессии идут сами (same-origin).
// region: 225=Россия, 213=Москва, 2=СПб. Период даёт график; таблица = последний месяц.
// Подробности и грабли логина/анти-завис браузера: references/wordstat-real-recipe.md
async () => {
  const REGION = "225";
  const phrases = [
    // <-- ВСТАВЬ СВОЙ СПИСОК ФРАЗ
    "агрегатор нейросетей",
    "нейросети для бизнеса",
  ];
  const out = {};
  for (const p of phrases) {
    try {
      const r = await fetch("https://wordstat.yandex.ru/wordstat/api/getTable", {
        method: "POST", credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          currentDevice: "desktop,phone,tablet", dbname: "rus",
          filters: { region: REGION, tableType: "popular" },
          searchValue: p, startDate: "01.06.2024", endDate: "31.05.2026"
        })
      });
      const j = await r.json();
      const pop = (((j.table || {}).tableData || {}).popular || [])
        .slice(0, 8).map(x => [x.text, parseInt(x.value, 10)]);
      out[p] = { total: j.totalValue ?? null, status: r.status, top: pop };
    } catch (e) { out[p] = { total: null, err: String(e).slice(0, 60) }; }
    await new Promise(s => setTimeout(s, 250)); // вежливая пауза против лимита
  }
  return out;
}
