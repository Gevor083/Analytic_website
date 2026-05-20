# 🔥 State-Managed Client-Side Engineering | Ֆրոնտենդի և UI Ճարտարապետություն

Modern users demand interactivity without seeing page flickers, full HTML re-paints, or janky JavaScript loading popups. This file explains how the User Interface (UI) bridges seamlessly with Django over lightweight `fetch()` API calls rather than relying on bulky multi-page architectures.

Ժամանակակից օգտատերերը պահանջում են ինտերակտիվություն՝ առանց էջի թարթումների, ամբողջական HTML վերբեռնումների կամ JavaScript-ի բեռնման անհարմար պատուհանների (popups) տեսնելու: Այս փաստաթուղթը բացատրում է, թե ինչպես է Օգտատիրոջ Ինտերֆեյսը (UI) սահուն կերպով կապվում Django-ի հետ թեթև `fetch()` API հարցումների միջոցով՝ փոխանակ հիմնվելու բազմաէջանի (multi-page) ծանր ճարտարապետությունների վրա:

---

## 🌓 State-Aware Dark Mode Engine | Կարգավիճակը Հիշող Մութ Ռեժիմի Շարժիչ (Dark Mode)

### 🇬🇧 English Explanation
Dark mode architectures often suffer from a noticeable bright "flash" when navigating between pages (the browser builds a white page locally, and then parses individual Javascript chunks half a second later to paint the DOM black). 

This project solves it via a **Backend Context Engine Sync**:
*   **Django Context Processor (`context_processors.py`)**: Intercepts every single HTTP template being constructed before it ever reaches the user. It explicitly injects a single dictionary item: `{'theme': request.session.get('theme', 'light')}` directly into the HTML context.
*   **Django Templating Engine**: `base.html` explicitly evaluates its root tag at the server level via `class="{% if theme == 'dark' %}dark-mode{% endif %}"`. The wait time to apply dark mode is exactly zero milliseconds.
*   **The Synchronized Client (`scripts.js`)**: If a user clicks the visual Sun/Moon toggle button, we invert the class natively on their live DOM (`document.body.classList.toggle('dark-mode')`) for instantaneous visual feedback. Simultaneously, we silently fire an AJAX `fetch()` POST containing `{ theme: 'dark' }` to the `/set_theme/` API backend to save the preference permanently.

### 🇦🇲 Հայերեն Բացատրություն
Մութ ռեժիմի ճարտարապետությունները հաճախ տառապում են նկատելի լուսավոր "բռնկումներով" (flash) էջերի միջև անցում կատարելիս (բրաուզերը նախ կառուցում է սպիտակ էջ տեղական համակարգում, իսկ հետո կես վայրկյան անց վերլուծում է Javascript-ի մասերը՝ DOM-ը սև գույնով ներկելու համար):

Այս նախագիծը լուծում է այս խնդիրը **Բեքենդի Կոնտեքստային Շարժիչի Համաժամացման (Backend Context Engine Sync)** միջոցով.
*   **Django Context Processor (`context_processors.py`).** Որսում է կառուցվող յուրաքանչյուր HTTP շաբլոն (template) նախքան այն կհասնի օգտատիրոջը: Այն անմիջապես ներարկում է ընդամենը մեկ բառարանային էլեմենտ՝ `{'theme': request.session.get('theme', 'light')}` անմիջապես HTML կոնտեքստի մեջ:
*   **Django Շաբլոնային Շարժիչ (Templating Engine).** `base.html`-ը գնահատում է իր արմատային (root) tag-ը հենց սերվերի մակարդակում՝ `class="{% if theme == 'dark' %}dark-mode{% endif %}"` կոդի միջոցով: Մութ ռեժիմը կիրառելու սպասման ժամանակը ճիշտ զրո միլիվայրկյան է:
*   **Համաժամացված Հաճախորդ (`scripts.js`).** Եթե օգտատերը սեղմում է Արև/Լուսին տեսողական կոճակը, մենք փոխում ենք class-ը ուղիղ նրանց կենդանի DOM-ում (`document.body.classList.toggle('dark-mode')`)՝ ակնթարթային տեսողական արձագանք ապահովելու համար: Միաժամանակ, մենք անձայն (silently) ուղարկում ենք AJAX `fetch()` POST հարցում, որը պարունակում է `{ theme: 'dark' }` դեպի `/set_theme/` API բեքենդ՝ նախընտրությունը մշտապես պահպանելու նպատակով:

---

## 🧑‍🎨 Interactive Drag and Drop Uploads | Ինտերակտիվ Քաշել-և-Գցել (Drag and Drop) Վերբեռնումներ

### 🇬🇧 English Explanation
The default web `input type="file"` is incredibly uninspired. Using HTML5 combined with ES6 event listeners, we deployed a custom interactive bounding box.

1. **`dragover` Initialization**: A massive dashed box wraps the input. Using `e.preventDefault()`, the browser ceases its default action (which is trying to forcefully open the file as a new tab).
2. **Dynamic UI Styling**: The bounding element receives `uploadZone.classList.add('dragover')`, scaling it dynamically, shifting the text color, and elevating the icon via simple CSS transforms for immediate hovering feedback.
3. **Data Pre-flight Analysis**: When the user drops a file, Javascript intercepts the file buffer explicitly prior to HTTP submittal. It validates `this.files[0].name.endsWith('.csv')` mapping appropriate iconography natively (displaying a stylized Excel or raw data JSON icon instead of a generic cloud).

### 🇦🇲 Հայերեն Բացատրություն
Վեբի ստանդարտ `input type="file"`-ը չափազանց անհետաքրքիր է: Օգտագործելով HTML5-ը՝ համակցված ES6 իրադարձությունների ունկնդիրների (event listeners) հետ, մենք ստեղծել ենք հատուկ ինտերակտիվ դաշտ վերբեռնումների համար:

1. **`dragover` Նախաստեղծում (Initialization).** Հսկայական կետագծերով արկղը շրջապատում է input-ը: Օգտագործելով `e.preventDefault()`, բրաուզերը դադարեցնում է իր լռելյայն (default) գործողությունը (որն է՝ փորձել ֆայլը բացել որպես նոր ներդիր):
2. **Դինամիկ UI Ոճավորում.** Շրջանակող էլեմենտը ստանում է `uploadZone.classList.add('dragover')` հրամանը, ինչը դինամիկ կերպով մեծացնում է այն, փոխում տեքստի գույնը և CSS տրանսֆորմացիաների միջոցով բարձրացնում է պատկերակը (icon)՝ վրան պահելիս ակնթարթային արձագանք ապահովելու համար:
3. **Տվյալների Նախնական Վերլուծություն.** Երբ օգտատերը գցում է ֆայլը, Javascript-ը որսում է ֆայլի բուֆերը նախքան HTTP հարցմամբ ուղարկելը: Այն ստուգում է `this.files[0].name.endsWith('.csv')` պայմանը՝ տեղադրելով համապատասխան պատկերակ (օրինակ՝ ցուցադրելով ոճավորված Excel կամ JSON տվյալների պատկերակ՝ ստանդարտ ամպի փոխարեն):

---

## 📈 Chart.js Data Visualization | Chart.js Տվյալների Վիզուալիզացիա (Արտապատկերում)

### 🇬🇧 English Explanation
Integrating robust Client-Side mathematical charting via Data Visualization.

**Why bypass Python's `Matplotlib` entirely?**
*   **Zero Server RAM Dependency**: Rendering 100 images via `matplotlib` concurrently easily crashes single-threaded servers by holding large objects in memory. Emitting 100 tiny `JSON` payloads over `/api/chart_data/` costs nearly zero RAM overhead.
*   **Interactivity**: Clients can natively hover over precise data nodes, click dynamic top legends to filter dataset noise out, intuitively scale axes boundaries, and gracefully interact with the chart directly in the browser.
*   **Graceful UX Handling**: If a 500 server error occurs inside the `fetch()` execution context due to mismatched parameters, the execution fails smoothly. The browser intercepts `.catch(err)` substituting the canvas with a clean `<div class="alert alert-danger">` inline block, completely safeguarding the parent page from crashing!

### 🇦🇲 Հայերեն Բացատրություն
Հաճախորդի կողմից (Client-Side) աշխատող մաթեմատիկական գծապատկերների հզոր ինտեգրում տվյալների վիզուալիզացիայի միջոցով:

**Ինչո՞ւ ամբողջությամբ շրջանցել Python-ի `Matplotlib`-ը:**
*   **Զրոյական Կախվածություն Սերվերի RAM-ից.** 100 նկար միաժամանակ արտապատկերելը `matplotlib`-ի միջոցով կարող է հեշտությամբ խափանել մեկ հոսքով (single-threaded) աշխատող սերվերները՝ պահելով մեծ օբյեկտներ հիշողության մեջ: Փոխարենը, 100 փոքրիկ `JSON` փաթեթներ `/api/chart_data/` API-ով ուղարկելը գրեթե զրոյական RAM է պահանջում:
*   **Ինտերակտիվություն.** Օգտատերերը կարող են մկնիկը պահել կոնկրետ տվյալների հանգույցների վրա, սեղմել վերին դինամիկ լեգենդների վրա՝ ավելորդ տվյալները ֆիլտրելու համար, ինտուիտիվ կերպով փոխել առանցքների (axes) սահմանները և գեղեցիկ կերպով փոխազդել գծապատկերի հետ անմիջապես բրաուզերում:
*   **Գեղեցիկ UX Կառավարում (Սխալների դեպքում).** Եթե անհամապատասխան պարամետրերի պատճառով `fetch()`-ի կատարման ընթացքում տեղի ունենա սերվերի 500 սխալ, գործընթացը կձախողվի սահուն կերպով: Բրաուզերը կորսա `.catch(err)` սխալը՝ փոխարինելով նկարչական դաշտը (canvas) մաքուր `<div class="alert alert-danger">` բլոկով, դրանով իսկ ամբողջությամբ ապահովագրելով հիմնական էջը խափանումներից (crash):
