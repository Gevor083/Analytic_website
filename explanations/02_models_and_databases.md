# 🗄️ Models & Database Architecture | Մոդելներ և Տվյալների Բազայի Ճարտարապետություն

At the heart of any solid Django application is its database structure. This project relies entirely on Django's ORM (Object-Relational Mapper) to map Python classes directly into SQL tables. The two primary custom models in this system are `UploadedFile` and `ProcessedData`. Let's understand how they interact.

Ցանկացած հզոր Django հավելվածի հիմքում ընկած է տվյալների բազայի կառուցվածքը: Այս նախագիծը ամբողջությամբ հիմնված է Django-ի ORM (Object-Relational Mapper) համակարգի վրա, որը Python դասերը (classes) ուղղակիորեն վերածում է SQL աղյուսակների: Այս համակարգում երկու հիմնական հատուկ մոդելներն են՝ `UploadedFile` (Ներբեռնված Ֆայլ) և `ProcessedData` (Մշակված Տվյալներ): Եկեք հասկանանք, թե ինչպես են դրանք փոխազդում:

---

## 1. `UploadedFile` Model | `UploadedFile` Մոդել

### 🇬🇧 English Explanation
This model acts as the "Parent" record. Every time a user completes a file upload, a new `UploadedFile` instance is created in the database.

**Key Responsibilities:**
*   **Storage Tracking:** Utilizes a `FileField` that tracks the physical location of the uploaded document inside the `uploads/` directory on the server.
*   **User Association:** Contains a `ForeignKey` linking the file securely to a specific authenticated Python `User`. If the user is anonymous, it remains `None`.
*   **State Management:** Booleans like `processed=True/False` help the frontend know if Celery has finished running mathematics on the file. If there's an error, it is stored in `error_message`.
*   **Metadata Caching:** Fields like `numeric_fields` and `categorical_fields` are cached as JSON strings so the application doesn't have to re-evaluate the CSV structure every time a user requests a new chart!

### 🇦🇲 Հայերեն Բացատրություն
Այս մոդելը հանդես է գալիս որպես "Ծնող" (Parent) գրառում: Ամեն անգամ, երբ օգտատերը ավարտում է ֆայլի վերբեռնումը, տվյալների բազայում ստեղծվում է նոր `UploadedFile` օբյեկտ:

**Հիմնական Գործառույթները.**
*   **Պահպանման Հետևում.** Օգտագործում է `FileField`, որը հետևում է վերբեռնված փաստաթղթի ֆիզիկական տեղադրությանը սերվերի `uploads/` թղթապանակում:
*   **Օգտատիրոջ Կապակցում.** Պարունակում է `ForeignKey`, որն ապահով կերպով կապում է ֆայլը կոնկրետ նույնականացված (authenticated) Python `User`-ի հետ: Եթե օգտատերը անանուն է, դաշտը մնում է `None`:
*   **Կարգավիճակի Կառավարում.** Բուլյան (Boolean) դաշտերը, ինչպիսիք են `processed=True/False`, օգնում են ֆրոնտենդին (frontend) իմանալ, արդյոք Celery-ն ավարտել է ֆայլի մաթեմատիկական մշակումը: Սխալի դեպքում այն պահպանվում է `error_message` դաշտում:
*   **Մետատվյալների Քեշավորում (Caching).** Դաշտերը, ինչպիսիք են `numeric_fields` (թվային դաշտեր) և `categorical_fields` (կատեգորիկ դաշտեր), պահպանվում են որպես JSON տողեր, որպեսզի հավելվածը ստիպված չլինի վերագնահատել CSV կառուցվածքը ամեն անգամ, երբ օգտատերը նոր գծապատկեր (chart) է պահանջում:

---

## 2. `ProcessedData` Model | `ProcessedData` Մոդել

### 🇬🇧 English Explanation
This model acts as the "Child" record. It has a rigorous `ForeignKey` mapping relationship back to `UploadedFile` (`on_delete=models.CASCADE`). 

**What does it do?**
When a heavy 100,000-row CSV file is analyzed by Pandas, we don't want to scan those 100,000 rows every time we load the results page. Instead, Celery extracts statistical summaries (aggregations) and saves them as individual `ProcessedData` rows. Usually, there is exactly **one `ProcessedData` row created per column** in the CSV file.

**Key Responsibilities:**
*   **Column Name Tracker:** Identifies which column this math belongs to (e.g., "Age", "Revenue").
*   **Stats JSON:** Stores mathematical derivations. E.g.: `{"mean": 45, "median": 42, "max": 120, "missing": 0}`. 
*   **Data Typer:** Categorizes columns as exactly "Numeric" or "Categorical/Object" to dictate which specific Charts are legally allowed to be generated for this dimension.

### 🇦🇲 Հայերեն Բացատրություն
Այս մոդելը հանդես է գալիս որպես "Երեխա" (Child) գրառում: Այն ունի խիստ `ForeignKey` կապ դեպի `UploadedFile` (`on_delete=models.CASCADE`):

**Ի՞նչ է այն անում։**
Երբ 100,000 տող ունեցող ծանր CSV ֆայլը վերլուծվում է Pandas-ի կողմից, մենք չենք ցանկանում սկանավորել այդ 100,000 տողերը ամեն անգամ արդյունքների էջը բեռնելիս: Փոխարենը, Celery-ն հանում է վիճակագրական ամփոփումներ (ագրեգացիաներ) և պահպանում դրանք որպես առանձին `ProcessedData` տողեր: Սովորաբար ստեղծվում է ճիշտ **մեկ `ProcessedData` տող՝ CSV ֆայլի յուրաքանչյուր սյունակի համար**:

**Հիմնական Գործառույթները.**
*   **Սյունակի Անվան Հետևում.** Նույնականացնում է, թե որ սյունակին են պատկանում հաշվարկները (օրինակ՝ "Տարիք", "Եկամուտ"):
*   **Վիճակագրության JSON.** Պահպանում է մաթեմատիկական արդյունքները: Օրինակ՝ `{"mean": 45, "median": 42, "max": 120, "missing": 0}`:
*   **Տվյալների Տեսակավորում (Typing).** Դասակարգում է սյունակները որպես խիստ "Թվային" կամ "Կատեգորիկ/Օբյեկտ", որպեսզի որոշի, թե հատկապես որ գծապատկերներն է թույլատրվում ստեղծել այս չափման (dimension) համար:

---

## ✨ Why this pattern is excellent | Ինչու է այս մոդելը հիանալի

### 🇬🇧 English Explanation
1. **Database Speed:** The Web Views (`views.py`) never touch the actual CSV file to render a page. The views simply query the `ProcessedData` objects utilizing standard SQL `SELECT` queries, which return instantly.
2. **Cascade Deletions:** Because of the strict `ForeignKey` mapping, when an `UploadedFile` expires or is deleted by the user, Postgres will immediately destroy all associated `ProcessedData` automatically, securing disk space. Orphaned data is impossible.

### 🇦🇲 Հայերեն Բացատրություն
1. **Տվյալների Բազայի Արագություն.** Web View-ները (`views.py`) էջը արտապատկերելու համար երբեք չեն դիպչում բուն CSV ֆայլին: Դրանք պարզապես հարցում են կատարում դեպի `ProcessedData` օբյեկտներ՝ օգտագործելով ստանդարտ SQL `SELECT` հարցումներ, որոնք ակնթարթորեն վերադարձնում են արդյունքը:
2. **Կասկադային Ջնջում (Cascade).** Խիստ `ForeignKey` կապի շնորհիվ, երբ `UploadedFile`-ի ժամկետը լրանում է կամ այն ջնջվում է օգտատիրոջ կողմից, Postgres-ը անմիջապես և ավտոմատ կերպով կոչնչացնի բոլոր կապակցված `ProcessedData` գրառումները՝ ազատելով սկավառակի հիշողությունը: Այսպիսով, անհնար է ունենալ որբ (orphaned) տվյալներ:
