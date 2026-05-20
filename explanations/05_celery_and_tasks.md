# ⚙️ Celery Workers & Asynchronous Tasks | Celery Աշխատողներ և Ասինխրոն Առաջադրանքներ

Data Science is computationally brutally expensive. If a massive 150MB `.CSV` file is given to Django, the synchronous parsing loop will lock the main thread, throwing Gunicorn errors, timing out NGINX, and dropping all other users from the website. The architecture avoids this via robust Asynchronous Job delegation.

Տվյալագիտությունը (Data Science) հաշվողական առումով խիստ ծախսատար է: Եթե 150 ՄԲ հսկայական `.CSV` ֆայլը տրվի Django-ին, սինխրոն մշակման ցիկլը կարգելափակի հիմնական հոսքը (main thread)՝ առաջացնելով Gunicorn-ի սխալներ, NGINX-ի timeout-ներ (ժամանակի սպառում) և կայքից դուրս կգցի բոլոր մյուս օգտատերերին: Ճարտարապետությունը խուսափում է սրանից՝ Ասինխրոն Առաջադրանքների (Asynchronous Job) հզոր պատվիրակման (delegation) միջոցով:

---

## 🏎️ The Request Lifecycle Engine | Հարցման Կենսացիկլի Շարժիչը (Request Lifecycle)

### 1. The Handoff | Փոխանցում (Handoff)

#### 🇬🇧 English Explanation
Instead of computing the CSV the moment `views.py` receives it, the server simply performs absolute immediate validation (size checks, malicious metadata headers). It executes `process_uploaded_file.delay(obj.id)`. This places a small, lightweight JSON descriptor string containing the Database ID of the file directly onto the **Redis Message Broker Layer**.

#### 🇦🇲 Հայերեն Բացատրություն
Փոխարենը մշակելու CSV ֆայլը հենց այն պահին, երբ `views.py`-ը ստանում է այն, սերվերը պարզապես իրականացնում է բացարձակ ակնթարթային ստուգումներ (չափի ստուգումներ, վնասակար մետատվյալների վերնագրեր): Այն կանչում է `process_uploaded_file.delay(obj.id)`: Սա տեղադրում է փոքր, թեթև JSON նկարագրող տող, որը պարունակում է ֆայլի Տվյալների Բազայի ID-ն, անմիջապես **Redis Հաղորդագրությունների Բրոքերի Շերտի (Message Broker Layer)** վրա:

### 2. The Redis Broker | Redis Բրոքեր

#### 🇬🇧 English Explanation
The Redis layer, operating entirely in-memory separately from Postgres, holds infinite "Queues". It guarantees exact-once delivery. It essentially "holds" tasks safely until an idle worker machine checks in.

#### 🇦🇲 Հայերեն Բացատրություն
Redis շերտը, որն աշխատում է ամբողջությամբ օպերատիվ հիշողության (in-memory) մեջ՝ Postgres-ից առանձին, պարունակում է անսահմանափակ "Հերթեր" (Queues): Այն երաշխավորում է ճշգրիտ մեկ անգամյա (exact-once) առաքում: Այն, ըստ էության, ապահով կերպով "պահում է" առաջադրանքները, մինչև որևէ ազատ (idle) worker մեքենա (հանգույց) կմիանա դրանք վերցնելու համար:

### 3. The Celery Worker Node (`tasks.py`) | Celery Աշխատող Հանգույց (Worker Node)

#### 🇬🇧 English Explanation
Operating fully detached from `views.py` (and potentially hosted on an entirely different scalable server globally), the independent Python script checks the queue stack. 

When it adopts `process_uploaded_file(file_id)`, here is the exact execution flow:
1. **Database Fetch:** Looks up the `UploadedFile` by its integer primary key.
2. **File I/O:** Opens physical file descriptors using Pandas (`pd.read_csv()`).
3. **Data Inference:** Iterates strictly over every column (inferring `data_type` logic conditionally).
4. **Calculations:** Evaluates IQR limits to spot potential outliers, calculates standard deviations, max, min, modes, and null gaps using vectorized operations (`numpy` arrays underneath) which are massively faster than raw Python loops.
5. **Database Commit:** Executes complex `bulk_create` Database commits via Django's ORM, bypassing traditional saving loop inefficiencies, storing everything exactly to `ProcessedData`. 
6. **Completion Signal:** Emits `file.processed = True` and writes `file.save()` back to Postgres.

#### 🇦🇲 Հայերեն Բացատրություն
Գործելով ամբողջությամբ անկախ `views.py`-ից (և հնարավոր է տեղադրված լինելով բոլորովին այլ, մասշտաբավորվող սերվերի վրա ցանկացած տեղ), այս անկախ Python սկրիպտը ստուգում է հերթերը:

Երբ այն վերցնում է `process_uploaded_file(file_id)` առաջադրանքը, ահա ճշգրիտ կատարման հոսքը.
1. **Տվյալների Բազայից Վերցնելը (Fetch).** Որոնում է `UploadedFile`-ը իր ամբողջական (integer) առաջնային բանալու (primary key) միջոցով:
2. **Ֆայլի Մուտք/Ելք (I/O).** Բացում է ֆիզիկական ֆայլը՝ օգտագործելով Pandas (`pd.read_csv()`):
3. **Տվյալների Վերլուծություն.** Խստորեն անցնում է յուրաքանչյուր սյունակի վրայով (որոշելով `data_type` տրամաբանությունը):
4. **Հաշվարկներ.** Գնահատում է IQR (Միջկվարտիլային տիրույթ) սահմանները՝ հնարավոր արտասովոր տվյալները (outliers) հայտնաբերելու համար, հաշվարկում է ստանդարտ շեղումներ, մաքսիմում, մինիմում, մոդ (mode) և դատարկ տիրույթներ՝ օգտագործելով վեկտորիզացված գործողություններ (`numpy` զանգվածներ), որոնք շատ ավելի արագ են, քան ստանդարտ Python ցիկլերը (loops):
5. **Տվյալների Բազայի Գրանցում (Commit).** Իրականացնում է բարդ `bulk_create` գրանցումներ տվյալների բազայում Django-ի ORM-ի միջոցով՝ շրջանցելով պահպանման ավանդական ցիկլերի անարդյունավետությունը, և պահպանում է ամեն ինչ ուղիղ `ProcessedData` մոդելում:
6. **Ավարտի Ազդանշան.** Սահմանում է `file.processed = True` և պահպանում այն նորից Postgres տվյալների բազայում `file.save()` հրամանով:

---

## 🔄 Front-End Polling Mechanisms | Ֆրոնտենդի Հարցման (Polling) Մեխանիզմներ

### 🇬🇧 English Explanation
When the user arrives on the `result_view()`, if `file_obj.processed` is `False`, the backend simply renders a beautiful HTML loading page ("File is still being processed"). Currently, users must manually refresh to see if the Celery worker has finished. 

**Future Improvements:**
To make this system extremely robust and modern, we could implement:
- **WebSocket Integration (Django Channels/Redis):** The frontend could subscribe to a channel. The exact millisecond Celery finishes, it sends a broadcast message to the socket, and the frontend instantly replaces the loading skeleton with the Data Table without any user reload. 
- **AJAX Long-Polling:** A simpler alternative where Javascript `setInterval()` pings an API endpoint every 3 seconds asking `is_processed=True?` and instantly reloading if configured.

### 🇦🇲 Հայերեն Բացատրություն
Երբ օգտատերը հասնում է `result_view()` էջին, և եթե `file_obj.processed` դաշտը `False` է, բեքենդը պարզապես արտապատկերում է գեղեցիկ HTML բեռնման էջ ("Ֆայլը դեռ մշակվում է"): Ներկայումս օգտատերերը պետք է ձեռքով թարմացնեն էջը՝ տեսնելու, արդյոք Celery աշխատողը ավարտել է գործը:

**Ապագա Բարելավումներ.**
Այս համակարգը չափազանց հզոր և ժամանակակից դարձնելու համար մենք կարող ենք իրականացնել.
- **WebSocket-ի Ինտեգրում (Django Channels/Redis).** Ֆրոնտենդը կարող է բաժանորդագրվել (subscribe) ալիքին: Այն ճշգրիտ միլիվայրկյանին, երբ Celery-ն ավարտում է աշխատանքը, այն հեռարձակում է (broadcast) հաղորդագրություն դեպի վեբ-սոքեթ (socket), և ֆրոնտենդը ակնթարթորեն փոխարինում է բեռնման էկրանը Տվյալների Աղյուսակով (Data Table)՝ առանց օգտատիրոջ կողմից էջի վերբեռնման (reload):
- **AJAX Long-Polling (Երկար Հարցումներ).** Ավելի պարզ այլընտրանք, որտեղ Javascript-ի `setInterval()`-ը յուրաքանչյուր 3 վայրկյանը մեկ հարցում (ping) է անում API վերջնակետին՝ հարցնելով `is_processed=True?`, և ակնթարթորեն վերբեռնում է էջը, եթե այո:

Այն պատճառով, որ հաշվարկները կատարվում են հիմնական հոսքից դուրս (off-grid), Django-ն մնում է կայծակնային արագությամբ գործող՝ հուսալիորեն և ակնթարթորեն սպասարկելով բոլոր ակտիվ օգտատերերի հարցումները:
