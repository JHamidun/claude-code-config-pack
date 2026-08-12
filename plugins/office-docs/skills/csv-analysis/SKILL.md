---
name: csv-analysis
description: Analyze CSV/Excel data files - statistics, visualization, transformations, insights
---

# CSV & Data Analysis Skill

## Overview

Навык для анализа табличных данных: CSV, Excel, JSON. Статистика, визуализация, трансформации.

## When to Use

- Анализ данных из CSV/Excel файлов
- Статистические расчёты
- Поиск аномалий и паттернов
- Создание отчётов по данным
- Data cleaning и preprocessing

## Instructions

### 1. Загрузка данных

```python
import pandas as pd

# CSV
df = pd.read_csv("data.csv")

# Excel
df = pd.read_excel("data.xlsx", sheet_name="Sheet1")

# JSON
df = pd.read_json("data.json")

# С параметрами
df = pd.read_csv("data.csv",
    encoding="utf-8",
    sep=";",
    decimal=",",
    parse_dates=["date_column"]
)
```

### 2. Первичный анализ

```python
# Обзор данных
print(df.head(10))
print(df.info())
print(df.describe())

# Типы данных
print(df.dtypes)

# Пропущенные значения
print(df.isnull().sum())

# Уникальные значения
print(df.nunique())
```

### 2.1 Профилирование датасета (до любых расчётов)

Прежде чем считать метрики, узнай **зерно** таблицы (одна строка — это что?), первичный ключ
и роль каждой колонки: идентификатор / измерение (для группировок) / метрика (для расчётов) /
дата / текст / флаг. От этого зависит, что вообще можно агрегировать.

```python
def profile(df):
    """Профиль: пропуски, кардинальность, тип колонки. Смотреть до расчётов."""
    n = len(df)
    rows = []
    for c in df.columns:
        nunique = df[c].nunique(dropna=True)
        rows.append({
            "column": c,
            "dtype": str(df[c].dtype),
            "null_pct": round(100 * df[c].isna().mean(), 2),
            "distinct": nunique,
            "card_ratio": round(nunique / n, 4) if n else 0,   # ~1.0 = ключ, <0.05 = измерение
            "top": df[c].mode().iloc[0] if not df[c].mode().empty else None,
            "top_freq_pct": round(100 * df[c].value_counts(normalize=True).iloc[0], 1)
                            if nunique else 0,
        })
    return pd.DataFrame(rows).sort_values("null_pct", ascending=False)

# Дубликаты по предполагаемому ключу — до того, как ключ пойдёт в merge
dupes = df[df.duplicated(subset=["entity_id"], keep=False)]
```

Пороги и сигналы:

- **Пропуски**: >5% — предупреждение, >20% — разобраться до расчётов, >20% пропусков в колонке-метрике делают среднее по ней непредставительным.
- **Кардинальность против ожидания**: `user_id` с 50 уникальными — джойн уже сломан либо это не тот файл; «категория» с 40 000 значений — там на самом деле свободный текст.
- **Одно значение занимает подозрительно большую долю** (`top_freq_pct`) — скорее всего это дефолт, подставленный вместо пропуска.
- **Значения-заглушки**: `0`, `-1`, `999999`, `"N/A"`, `"TBD"`, `"test"`, `"xxx"`, даты в 1970 и в будущем.
- **Несогласованные форматы одного и того же**: `"USA" / "US" / "United States" / "us"`, хвостовые пробелы, разный регистр, числа строками.
- **Нарушения бизнес-правил**: отрицательные количества, дата окончания раньше начала, проценты > 100, `status='completed'` при пустом `completed_at`.
- **Округлённость**: все значения кратны 5 или 10 — это оценки, а не измерения.

```python
# Быстрые проверки формата и заглушек
placeholders = ["N/A", "TBD", "test", "xxx", "-", "null", "None"]
df.select_dtypes("object").apply(lambda s: s.isin(placeholders).sum())
df.select_dtypes("object").apply(lambda s: (s != s.str.strip()).sum())   # хвостовые пробелы
df["date"].max(), (df["date"] > pd.Timestamp.now()).sum()                # даты из будущего
```

### 3. Статистика

> Как выбирать и трактовать цифры (среднее против медианы, перцентили, тренды и сезонность,
> проверка гипотез, ловушки — Симпсон, ошибка выжившего, множественные сравнения) —
> `references/stats-methodology.md`. Код ниже, методология там.

```python
# Базовая статистика
mean = df["column"].mean()
median = df["column"].median()
std = df["column"].std()
min_val = df["column"].min()
max_val = df["column"].max()

# Группировка
grouped = df.groupby("category").agg({
    "value": ["mean", "sum", "count"],
    "price": ["min", "max"]
})

# Корреляция
correlation = df.corr()
```

### 4. Data Cleaning

```python
# Удаление дубликатов
df = df.drop_duplicates()

# Заполнение пропусков
df["column"].fillna(df["column"].mean(), inplace=True)
df["column"].fillna("Unknown", inplace=True)

# Удаление пропусков
df = df.dropna(subset=["important_column"])

# Типы данных
df["date"] = pd.to_datetime(df["date"])
df["value"] = pd.to_numeric(df["value"], errors="coerce")
```

### 5. Фильтрация и выборка

```python
# Фильтры
filtered = df[df["value"] > 100]
filtered = df[(df["category"] == "A") & (df["value"] > 50)]
filtered = df[df["name"].str.contains("keyword", case=False)]

# Top N
top_10 = df.nlargest(10, "value")
bottom_10 = df.nsmallest(10, "value")

# Сэмплирование
sample = df.sample(n=100)
sample = df.sample(frac=0.1)
```

### 6. Трансформации

```python
# Новые колонки
df["total"] = df["price"] * df["quantity"]
df["category"] = df["value"].apply(lambda x: "high" if x > 100 else "low")

# Pivot table
pivot = df.pivot_table(
    values="sales",
    index="region",
    columns="product",
    aggfunc="sum"
)

# Merge
merged = pd.merge(df1, df2, on="id", how="left")
```

### 7. Экспорт

```python
# CSV
df.to_csv("output.csv", index=False)

# Excel
df.to_excel("output.xlsx", index=False, sheet_name="Data")

# JSON
df.to_json("output.json", orient="records")
```

## Examples

### Пример 1: Анализ продаж

```python
# Загрузка
df = pd.read_csv("sales.csv")

# Статистика по регионам
by_region = df.groupby("region").agg({
    "amount": ["sum", "mean", "count"],
    "profit": "sum"
}).round(2)

# Top продукты
top_products = df.groupby("product")["amount"].sum().nlargest(10)

# Тренд по месяцам
df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
monthly = df.groupby("month")["amount"].sum()
```

### Пример 2: Поиск аномалий

```python
# Z-score для выбросов
from scipy import stats
z_scores = stats.zscore(df["value"])
outliers = df[abs(z_scores) > 3]

# IQR метод
Q1 = df["value"].quantile(0.25)
Q3 = df["value"].quantile(0.75)
IQR = Q3 - Q1
outliers = df[(df["value"] < Q1 - 1.5*IQR) | (df["value"] > Q3 + 1.5*IQR)]
```

## Dependencies

```bash
pip install pandas openpyxl xlrd scipy
```

## Tips

1. **Всегда начинай** с `df.info()` и `df.describe()`
2. **Проверяй типы** данных перед анализом
3. **Обрабатывай пропуски** до расчётов
4. **Используй groupby** для агрегации
5. **Сохраняй промежуточные** результаты
