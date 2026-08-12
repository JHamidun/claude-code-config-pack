queue = []

# 1. Tier S: in CRM AND touch_count > 0
for inn in bitrix_data["by_inn"]:
    info = bitrix_data["by_inn"][inn]
    if info["touch_count"] > 0:
        queue.append({"tier": "S", "inn": inn, "name": ..., "reason": f"Активная история. {products}, last_touch={info['last_touch']}"})

# 2. Tier B: in CRM, no touches
    else:
        queue.append({"tier": "B", "inn": inn, "name": ..., "reason": "В Bitrix как карточка, без касаний"})

# 3. Tier A: NOT in CRM, top N by rev2024
cold = [r for r in extracted if r["inn"] not in bitrix_data["by_inn"] and r.get("rev2024")]
cold.sort(key=lambda r: -r["rev2024"])
for r in cold[:limit]:
    queue.append({"tier": "A", "inn": r["inn"], "name": r["name"], "reason": f"Холодняк, выручка 2024: {rev:,.0f}"})
