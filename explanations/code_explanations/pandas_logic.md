# 🐼 Code Deep Dive: Pandas Processing in `tasks.py` | Կոդի Խորը Ուսումնասիրություն. Pandas-ի Մշակումը `tasks.py`-ում

This document breaks down the most computationally intensive function in the entire application: `process_uploaded_file()`.

Այս փաստաթուղթը վերլուծում է ամբողջ հավելվածի ամենաշատ հաշվողական ռեսուրս պահանջող ֆունկցիան՝ `process_uploaded_file()`:

---

## The Chunking Strategy | Մասնատման (Chunking) Ռազմավարությունը

### 🇬🇧 English Explanation
```python
df_iterator = _make_iterator(file_obj, file_type, use_path, full_df, chunk_size=10_000)
for chunk in df_iterator:
    # Processing logic
```
If a user uploads a 5,000,000 row CSV, loading it entirely into RAM might consume 4GB of memory, instantly crashing the Celery worker. By passing `chunksize=10_000` to `pandas.read_csv()`, Pandas returns an iterator. It only loads 10,000 rows into memory at a time, calculates the math, throws away the rows from RAM, and loads the next 10,000. This is called **O(1) Memory Complexity** parsing.

### 🇦🇲 Հայերեն Բացատրություն
Եթե օգտատերը վերբեռնում է 5,000,000 տողանոց CSV ֆայլ, այն ամբողջությամբ օպերատիվ հիշողության (RAM) մեջ բեռնելը կարող է սպառել 4 ԳԲ հիշողություն՝ ակնթարթորեն խափանելով Celery worker-ը: `pandas.read_csv()` ֆունկցիային փոխանցելով `chunksize=10_000`՝ Pandas-ը վերադարձնում է իտերատոր: Այն միաժամանակ հիշողության մեջ բեռնում է միայն 10,000 տող, հաշվարկում է մաթեմատիկան, մաքրում է այդ տողերը հիշողությունից և բեռնում հաջորդ 10,000-ը: Սա կոչվում է պարսինգ (parsing) **O(1) Հիշողության Բարդությամբ**:

---

## Vectorized Mathematical Aggregation | Վեկտորիզացված Մաթեմատիկական Ագրեգացիա

### 🇬🇧 English Explanation
```python
stats['sum'] += float(non_null.astype(float).sum())
stats['sum_sq'] += float((non_null.astype(float) ** 2).sum())
```
Because we process in chunks, we cannot simply use `.mean()` on the whole file. Instead, we use a streaming algorithm for standard deviation and mean. We accumulate the `sum`, the `count`, and the `sum of squares (sum_sq)`. 

At the very end of the file, we mathematically derive the final stats:
`mean = stats['sum'] / stats['count']`
`variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)`

This relies on NumPy's C-level vectorization (`astype(float) ** 2`), which applies the exponentiation to 10,000 items simultaneously in memory, running hundreds of times faster than a standard Python `for x in array:` loop.

### 🇦🇲 Հայերեն Բացատրություն
Քանի որ մենք տվյալները մշակում ենք մասերով (chunks), մենք չենք կարող պարզապես օգտագործել `.mean()` ամբողջ ֆայլի համար: Փոխարենը, մենք օգտագործում ենք հոսքային (streaming) ալգորիթմ՝ ստանդարտ շեղումը և միջինը հաշվելու համար: Մենք կուտակում ենք գումարը (`sum`), քանակը (`count`) և քառակուսիների գումարը (`sum of squares` կամ `sum_sq`):

Ֆայլի ամենավերջում մենք մաթեմատիկորեն դուրս ենք բերում վերջնական վիճակագրությունը.
`միջին (mean) = stats['sum'] / stats['count']`
`դիսպերսիա (variance) = (stats['sum_sq'] / stats['count']) - (mean ** 2)`

Սա հիմնված է NumPy-ի C լեզվի մակարդակի վեկտորիզացիայի վրա (`astype(float) ** 2`), որը ցուցիչի բարձրացումը կիրառում է 10,000 էլեմենտի վրա միաժամանակ հիշողության մեջ՝ աշխատելով հարյուրավոր անգամներ ավելի արագ, քան ստանդարտ Python `for x in array:` ցիկլը:

---

## Outlier Detection via IQR | Արտասովոր Տվյալների (Outliers) Հայտնաբերում IQR-ով

### 🇬🇧 English Explanation
The `detect_outliers_iqr()` function analyzes the random sample size we collected.
*   **Q1:** 25th Percentile
*   **Q3:** 75th Percentile
*   **IQR:** `Q3 - Q1`
Anything falling below `Q1 - 1.5*IQR` or above `Q3 + 1.5*IQR` is statistically flagged as an anomaly. This is crucial for Data Science pipelines to detect corrupt sensors, fraudulent financial entries, or broken database exports automatically.

### 🇦🇲 Հայերեն Բացատրություն
`detect_outliers_iqr()` ֆունկցիան վերլուծում է մեր հավաքած պատահական նմուշները (sample size):
*   **Q1.** 25-րդ տոկոսադրույք (Percentile)
*   **Q3.** 75-րդ տոկոսադրույք
*   **IQR.** `Q3 - Q1` (Միջկվարտիլային տիրույթ)
Ցանկացած արժեք, որն ընկնում է `Q1 - 1.5*IQR`-ից ներքև կամ `Q3 + 1.5*IQR`-ից վերև, վիճակագրորեն նշվում է որպես անոմալիա: Սա խիստ կարևոր է Տվյալագիտության (Data Science) համակարգերում՝ ավտոմատ կերպով հայտնաբերելու փչացած սենսորները, կեղծ ֆինանսական գրառումները կամ վնասված տվյալների արտահանումները:
