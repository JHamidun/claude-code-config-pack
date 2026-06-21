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

### 3. Статистика

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
