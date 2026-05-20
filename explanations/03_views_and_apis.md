# 📂 Core Backend Logic: `analytics_app/views.py` | Հիմնական Բեքենդի Տրամաբանությունը. `analytics_app/views.py`

When working with data-heavy applications, keeping views thin and logic separate makes a huge difference in maintainability.

Տվյալներով ծանրաբեռնված հավելվածների հետ աշխատելիս, view-ները (տեսքերը) թեթև պահելը և տրամաբանությունը առանձնացնելը հսկայական դեր ունի հեշտ սպասարկման (maintainability) հարցում:

---

## Fat Views vs. Thin Views (The Golden Rule) | Ծանր View-ներ ընդդեմ Թեթև View-ների (Ոսկե Կանոն)

### 🇬🇧 English Explanation
In Django, `views.py` is simply a traffic controller. A request comes in via an HTTP method (GET, POST), and the view should **only** be responsible for routing that request, triggering a function, checking authentication, and returning an HTTP Response. 

**Anti-Pattern:** Fat Views contain 2,000 lines of data science code, DataFrame operations, API calls, error catches, file processing chunks, and raw SQL queries grouped together. This is impossible to test, debug, or read.

**Modern Architecture:** Thin views simply map incoming requests to dedicated files like `services.py` or `.delay()` tasks in Celery. 

### 🇦🇲 Հայերեն Բացատրություն
Django-ում `views.py`-ը պարզապես երթևեկության վերահսկիչ է (traffic controller): Հարցումը գալիս է HTTP մեթոդով (GET, POST), և view-ն պետք է **միայն** պատասխանատու լինի այդ հարցումը ուղղորդելու, ֆունկցիա կանչելու, նույնականացումը (authentication) ստուգելու և HTTP պատասխան վերադարձնելու համար:

**Սխալ Մոտեցում (Anti-Pattern).** Ծանր View-ները (Fat Views) պարունակում են տվյալագիտության 2000 տողանոց կոդ, DataFrame-ի գործողություններ, API կանչեր, սխալների որսում, ֆայլերի մշակման բլոկներ և հում SQL հարցումներ միասին խմբավորված: Սա անհնար է դարձնում կոդի թեստավորումը, վրիպազերծումը (debugging) կամ ընթերցումը:

**Ժամանակակից Ճարտարապետություն.** Թեթև View-ները (Thin Views) պարզապես մուտքային հարցումները ուղղորդում են առանձնացված ֆայլերի (ինչպես օրինակ՝ `services.py`) կամ Celery-ի `.delay()` առաջադրանքների (tasks):

---

## 🛠 Active API Endpoints | Գործող API Վերջնակետեր (Endpoints)

We upgraded the application from a multi-page routing framework to a single-page interactive app (SPA) using **JSON APIs** instead of heavy HTML template responses.

Մենք թարմացրել ենք հավելվածը բազմաէջանի (multi-page) երթուղային ֆրեյմվորքից դեպի մեկ էջանոց ինտերակտիվ հավելված (SPA)՝ օգտագործելով **JSON API-ներ**՝ ծանր HTML շաբլոնային պատասխանների փոխարեն:

### 1. `chart_data_api(request, file_id)`

#### 🇬🇧 English Explanation
This is the single most important view in the app! 
*   **Method:** HTTP GET
*   **How it works:** Expects query parameters (e.g., `?chart_type=pie&x_axis=Department`).
*   **The Backend Logic:** It queries the database, extracts a tiny targeted subset of the required Pandas DataFrame (`df[x_axis]`), sanitizes `NaN` objects (because JSON syntax crashes if it receives a `NaN` float type), and wraps it cleanly into a JSON object `{"labels": [...], "data": [...]}`.
*   **Why?** This prevents Python's Matplotlib from destroying server RAM by generating images backend, and instead allows `Chart.js` to animate interactive charts gracefully on the user's browser via a simple Javascript `fetch()`.

#### 🇦🇲 Հայերեն Բացատրություն
Սա հավելվածի ամենակարևոր view-ն է:
*   **Մեթոդ.** HTTP GET
*   **Ինչպես է այն աշխատում.** Սպասում է հարցման պարամետրեր (օրինակ՝ `?chart_type=pie&x_axis=Department`):
*   **Բեքենդի Տրամաբանությունը.** Այն հարցում է անում տվյալների բազային, հանում է անհրաժեշտ Pandas DataFrame-ի միայն փոքր, թիրախավորված մասը (`df[x_axis]`), մաքրում է `NaN` (դատարկ) օբյեկտները (քանի որ JSON շարահյուսությունը խափանվում է, եթե ստանում է `NaN` float տիպ), և մաքուր կերպով այն փաթեթավորում է JSON օբյեկտում՝ `{"labels": [...], "data": [...]}`:
*   **Ինչո՞ւ։** Սա կանխում է, որպեսզի Python-ի Matplotlib-ը չսպառի սերվերի օպերատիվ հիշողությունը (RAM)` նկարներ գեներացնելով բեքենդում: Փոխարենը, այն թույլ է տալիս, որ `Chart.js`-ը գեղեցիկ անիմացիաներով ցուցադրի ինտերակտիվ գծապատկերները օգտատիրոջ բրաուզերում՝ օգտագործելով պարզ Javascript `fetch()`:

### 2. `set_theme(request)`

#### 🇬🇧 English Explanation
Handles our Dark/Light Mode state! 
*   **Method:** HTTP POST
*   **Security:** Mandates `X-CSRFToken` in the headers. 
*   **How it works:** It extracts the user's preference payload from the Javascript `fetch` body, then permanently writes `request.session['theme'] = 'dark'`. 
*   **The Power:** Because Django controls the initial HTML render, every subsequent page the user loads will naturally, instantly, and natively load dark-mode CSS classes from the first millisecond because of our Context Processors synchronizing with this API!

#### 🇦🇲 Հայերեն Բացատրություն
Կառավարում է մեր Մութ/Լուսավոր (Dark/Light) ռեժիմը:
*   **Մեթոդ.** HTTP POST
*   **Անվտանգություն.** Պահանջում է `X-CSRFToken` հարցման վերնագրերում (headers):
*   **Ինչպես է այն աշխատում.** Այն հանում է օգտատիրոջ նախընտրության տվյալները Javascript `fetch`-ի մարմնից, այնուհետև մշտապես գրանցում է `request.session['theme'] = 'dark'`:
*   **Առավելությունը.** Քանի որ Django-ն է կառավարում սկզբնական HTML արտապատկերումը, օգտատիրոջ կողմից բեռնվող յուրաքանչյուր հաջորդ էջ բնական, ակնթարթային և վայրկյանական կերպով կբեռնի մութ ռեժիմի CSS դասերը (classes) առաջին իսկ միլիվայրկյանից, քանի որ մեր Context Processor-ները համաժամացված (synchronized) են այս API-ի հետ:

---

## 🛑 Validation and Upload Restrictions | Ստուգումներ և Վերբեռնման Սահմանափակումներ

### 🇬🇧 English Explanation
The `upload_view()` is heavily guarded because File I/O operations are the #1 source of server hacks. 

1. **Size Enforcement:** `if uploaded_file.size > settings.MAX_UPLOAD_SIZE:` immediately throws out files exceeding 30MB without passing them to memory or Pandas to prevent buffer-overflow DDoS attacks.
2. **Type Enforcement:** Only permits strict whitelists of `.csv`, `.json`, and `.xlsx`. 
3. **Data Uniformity Conversion:** If an Excel document (`.xlsx`) or JSON dictionary (`.json`) slips through, the code executes an incredibly clever in-memory conversion block utilizing `io.StringIO()`. It maps every single schema back to a standardized flat CSV buffer, saving the exact CSV directly to the filesystem before uploading. This drastically simplifies Celery tasks because the worker node only ever has to know how to process a single file type: CSV!

### 🇦🇲 Հայերեն Բացատրություն
`upload_view()`-ն խստորեն պաշտպանված է, քանի որ Ֆայլերի Մուտքի/Ելքի (File I/O) գործողությունները սերվերի հաքերային հարձակումների հիմնական (թիվ 1) աղբյուրն են:

1. **Չափի Վերահսկում.** `if uploaded_file.size > settings.MAX_UPLOAD_SIZE:` պայմանը անմիջապես մերժում է 30 ՄԲ-ը գերազանցող ֆայլերը՝ առանց դրանք հիշողություն կամ Pandas փոխանցելու, ինչը կանխում է buffer-overflow (բուֆերի գերլցման) DDoS հարձակումները:
2. **Տիպի Վերահսկում.** Թույլատրվում են միայն խիստ սպիտակ ցուցակում (whitelist) գտնվող `.csv`, `.json` և `.xlsx` ձևաչափերը:
3. **Տվյալների Համասեռության Փոխարկում.** Եթե բեռնվում է Excel փաստաթուղթ (`.xlsx`) կամ JSON բառարան (`.json`), կոդը իրականացնում է չափազանց խելացի՝ հիշողության մեջ (in-memory) փոխարկման բլոկ՝ օգտագործելով `io.StringIO()`: Այն բոլոր սխեմաները վերափոխում է ստանդարտացված հարթ (flat) CSV բուֆերի՝ պահպանելով այն անմիջապես ֆայլային համակարգում վերբեռնելուց առաջ: Սա կտրուկ պարզեցնում է Celery առաջադրանքների աշխատանքը, քանի որ worker հանգույցը պետք է իմանա միայն մեկ ֆայլի տեսակ մշակելու ձև՝ CSV:
