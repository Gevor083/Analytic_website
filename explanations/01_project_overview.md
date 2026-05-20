# 🏢 Architecture Stack Explained | Ճարտարապետական Ստեկի Բացատրություն

Welcome to the **Analytics Website** codebase. This file explains the rationale behind our technology stack, detailing why specific tools were adopted over others to build a robust, scalable, and high-performance data ingestion platform.

Բարի գալուստ **Analytics Website** (Վերլուծական Կայք) նախագծի կոդային բազա։ Այս փաստաթուղթը բացատրում է մեր տեխնոլոգիական ստեկի տրամաբանությունը՝ մանրամասնելով, թե ինչու են ընտրվել հատկապես այս գործիքները՝ ստեղծելու համար հզոր, մասշտաբավորվող և բարձր արդյունավետությամբ տվյալների մշակման հարթակ:

---

## 🐍 Backend Core: Django | Բեքենդի Միջուկ. Django

### 🇬🇧 English Explanation
*   **The Problem:** Building standard APIs, managing User ORM tokens, executing secure Authentication schemas, and connecting to a PostgreSQL database securely often takes hundreds of hours to write from scratch when using minimalist frameworks like NodeJS or Flask. You are forced to manually handle routing, security, and database sessions.
*   **The Solution:** `Django`. It provides an impenetrable, "batteries-included" MVC (Model-View-Template) framework. Django comes with built-in CSRF (Cross-Site Request Forgery) protection, automatic SQL Injection sanitization, and User Session handling out of the box. This allows developers to skip boilerplate code and focus strictly on the core business logic—specifically, the Data Science and Analytics integrations.

### 🇦🇲 Հայերեն Բացատրություն
*   **Խնդիրը.** Ստանդարտ API-ների կառուցումը, օգտատերերի ORM տոկենների կառավարումը, անվտանգ նույնականացման (Authentication) սխեմաների իրականացումը և PostgreSQL տվյալների բազայի հետ ապահով կապի ստեղծումը հաճախ պահանջում է հարյուրավոր ժամեր, երբ օգտագործվում են մինիմալիստական ֆրեյմվորքներ, ինչպիսիք են NodeJS-ը կամ Flask-ը: Դուք ստիպված եք լինում ձեռքով կառավարել անվտանգությունը, երթուղիները (routing) և տվյալների բազայի սեսիաները:
*   **Լուծումը.** `Django`: Այն տրամադրում է հզոր և "ամեն ինչ ներառող" MVC (Model-View-Template) ֆրեյմվորք: Django-ն ունի ներկառուցված CSRF պաշտպանություն, ավտոմատ պաշտպանություն SQL Injection-ներից և օգտատերերի սեսիաների կառավարման համակարգ անմիջապես տեղադրման պահից: Սա թույլ է տալիս ծրագրավորողներին շրջանցել ստանդարտ (բոյլերփլեյթ) կոդի գրումը և կենտրոնանալ բացառապես բիզնես տրամաբանության՝ հատկապես Data Science-ի և Վերլուծությունների (Analytics) ինտեգրման վրա:

---

## 💾 Relational Database: PostgreSQL | Հարաբերական Տվյալների Բազա. PostgreSQL

### 🇬🇧 English Explanation
*   **The Problem:** Unstructured NoSQL databases (like MongoDB) fall apart when you need perfect relational mapping. For example, if you need to perfectly link one `UploadedFile` record to 500 individual rows of `ProcessedData` columns, and automatically `CASCADE` delete all 500 rows if the parent file is eventually deleted, NoSQL requires manual cleanup logic which is error-prone.
*   **The Solution:** `PostgreSQL` paired with `psycopg2`. Postgres offers flawless referential integrity, ACID compliance, and advanced indexing capabilities. The relational architecture ensures that our massive datasets remain perfectly structured, linked, and clean without orphaned rows.

### 🇦🇲 Հայերեն Բացատրություն
*   **Խնդիրը.** Չկառուցվածքավորված NoSQL տվյալների բազաները (օրինակ՝ MongoDB) հարմար չեն, երբ անհրաժեշտ է իդեալական հարաբերական կապավորում: Օրինակ, երբ պետք է կապել մեկ `UploadedFile` (Ներբեռնված Ֆայլ) գրառումը `ProcessedData` (Մշակված Տվյալներ) մոդելի 500 տողերի հետ և ավտոմատ կերպով ջնջել (CASCADE) այդ բոլոր 500 տողերը, եթե հիմնական ֆայլը ջնջվում է, NoSQL-ը պահանջում է ձեռքով մաքրման տրամաբանություն, ինչը հակված է սխալների:
*   **Լուծումը.** `PostgreSQL`՝ համակցված `psycopg2` գրադարանի հետ: Postgres-ը առաջարկում է անթերի հարաբերական ամբողջականություն, ACID ստանդարտներին համապատասխանություն և ինդեքսավորման առաջադեմ հնարավորություններ: Հարաբերական ճարտարապետությունը երաշխավորում է, որ մեր հսկայական տվյալները կմնան կատարելապես կառուցվածքավորված, կապակցված և մաքուր:

---

## 🐼 Mathematics & Data Mapping: Pandas & NumPy | Մաթեմատիկա և Տվյալների Մշակում. Pandas և NumPy

### 🇬🇧 English Explanation
*   **The Problem:** Using standard Python `for loops` to iterate through an array representing a CSV file with 2,000,000 rows takes roughly two to three minutes to process. Python's native data structures are heavily generalized and notoriously slow for bulk mathematical computations.
*   **The Solution:** `pandas` powered by `numpy`. NumPy bindings drop explicitly into low-level C programming. The exact same 2,000,000 row calculations are evaluated in roughly 300 milliseconds because the mathematics are applied using advanced, contiguous memory array vectorizations. This makes data parsing and statistical calculations blazing fast.

### 🇦🇲 Հայերեն Բացատրություն
*   **Խնդիրը.** Ստանդարտ Python `for` ցիկլերի օգտագործումը 2,000,000 տող ունեցող CSV ֆայլի զանգվածի վրայով անցնելու համար պահանջում է մոտ երկուսից երեք րոպե ժամանակ: Python-ի ստանդարտ տվյալների կառույցները շատ ընդհանրացված են և հայտնի են իրենց դանդաղությամբ մեծածավալ մաթեմատիկական հաշվարկների դեպքում:
*   **Լուծումը.** `pandas`՝ ապահովված `numpy`-ի հզորությամբ: NumPy-ի կապերը (bindings) իջնում են մինչև ցածր մակարդակի C ծրագրավորման շերտ: Ճիշտ նույն 2,000,000 տողանոց հաշվարկները կատարվում են մոտ 300 միլիվայրկյանում, քանի որ մաթեմատիկան կիրառվում է առաջադեմ վեկտորիզացված զանգվածների միջոցով, որոնք զբաղեցնում են հարակից հիշողության բլոկներ: Սա դարձնում է տվյալների մշակումը և վիճակագրական հաշվարկները աներևակայելի արագ:

---

## 📨 Queue Broker: Celery & Redis | Հերթերի Բրոքեր. Celery և Redis

### 🇬🇧 English Explanation
*   **The Problem:** A user uploads a massive 50MB file. If Django begins iterating through the file synchronously to find outliers immediately, that specific user (and likely the NGINX host running the entire server) gets locked in a synchronous blocking loop for 10-20 seconds. Other users will experience server lag.
*   **The Solution:** An asynchronous messaging layer (`Redis`) combined with background workers (`Celery`). When a file is uploaded, Django says "Hey Redis, hold this File ID in the queue," and instantly returns an HTML response: "Processing in background." An idle Celery worker grabs the ID from Redis, runs the heavy Pandas data analysis completely separate from the main web server, and saves it. The core website never blocks and remains snappy.

### 🇦🇲 Հայերեն Բացատրություն
*   **Խնդիրը.** Օգտատերը վերբեռնում է հսկայական 50 ՄԲ ֆայլ: Եթե Django-ն սկսի սինխրոն կերպով մշակել ֆայլը՝ արտասովոր տվյալներ (outliers) գտնելու համար, այդ կոնկրետ օգտատերը (և հավանաբար NGINX սերվերը) կարգելափակվի սինխրոն ցիկլում 10-20 վայրկյանով: Այլ օգտատերեր նույնպես կզգան սերվերի դանդաղում:
*   **Լուծումը.** Ասինխրոն հաղորդագրությունների շերտ (`Redis`)՝ համակցված ֆոնային աշխատողների (workers) հետ (`Celery`): Երբ ֆայլը վերբեռնվում է, Django-ն ասում է. "Հեյ Redis, պահիր այս ֆայլի ID-ն հերթում", և ակնթարթորեն վերադարձնում է պատասխան օգտատիրոջը. "Մշակվում է ֆոնային ռեժիմում": Ազատ Celery աշխատողը վերցնում է ID-ն Redis-ից, կատարում է ծանր Pandas տվյալների վերլուծությունը հիմնական վեբ սերվերից ամբողջությամբ առանձնացված և պահպանում այն: Հիմնական կայքը երբեք չի արգելափակվում և մնում է չափազանց արագ:

---

## 🪟 Javascript & Front-End Architecture | Javascript և Front-End Ճարտարապետություն

### 🇬🇧 English Explanation
*   **The Problem:** Modern Users demand interactivity. They expect dynamic dashboards, smooth transitions, and instant feedback without seeing page flickers or full HTML re-paints on every click.
*   **The Solution:** We combined standard HTML5 styling using `CSS3 / Bootstrap 5` with vanilla ES6 Javascript. This keeps our frontend bundle small without the massive overhead of React or Vue, while still providing modern interactivity.
*   **The Visualization (Chart.js):** Instead of using Matplotlib (which holds an active Python memory instance open for every single chart image rendered on the backend), we use simple REST API queries (`/api/chart_data/`). These APIs return lightning-fast `JSON` datasets directly to the browser. This allows the client's own GPU/CPU to render the canvas graphs directly using `Chart.js`, significantly lowering our server costs and dramatically speeding up the user experience.

### 🇦🇲 Հայերեն Բացատրություն
*   **Խնդիրը.** Ժամանակակից օգտատերերը պահանջում են ինտերակտիվություն: Նրանք ակնկալում են դինամիկ վահանակներ, սահուն անցումներ և ակնթարթային արձագանք՝ առանց էջի թարթելու կամ ամեն սեղմումից հետո ամբողջական HTML վերբեռնման սպասելու:
*   **Լուծումը.** Մենք համատեղել ենք ստանդարտ HTML5 ոճավորումը `CSS3 / Bootstrap 5`-ի միջոցով և մաքուր (vanilla) ES6 Javascript-ը: Սա պահում է մեր ֆրոնտենդի ծավալը փոքր՝ առանց React-ի կամ Vue-ի ավելորդ ծանրաբեռնվածության, միևնույն ժամանակ ապահովելով ժամանակակից ինտերակտիվություն:
*   **Վիզուալիզացիան (Chart.js).** Փոխարենը օգտագործելու Matplotlib (որը բաց է պահում ակտիվ Python հիշողության օբյեկտ բեքենդում ստեղծված ամեն մի գծապատկերի նկարի համար), մենք օգտագործում ենք պարզ REST API հարցումներ (`/api/chart_data/`): Այս API-ները վերադարձնում են շատ արագ `JSON` տվյալներ ուղիղ բրաուզերին: Սա թույլ է տալիս հաճախորդի սեփական համակարգչի GPU/CPU-ին ուղղակիորեն նկարել գրաֆիկները՝ օգտագործելով `Chart.js`: Արդյունքում, էապես նվազում են մեր սերվերի ծախսերը և կտրուկ արագանում է օգտագործողի փորձառությունը:
