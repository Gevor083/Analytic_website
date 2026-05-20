# 🧪 Testing Strategy (`tests.py`) | Թեստավորման Ռազմավարություն (`tests.py`)

A massive `19KB` test suite ensures our application remains stable during future updates. We use Django's native `TestCase` framework.

Մեր հսկայական `19KB` ծավալով թեստավորման հավաքածուն ապահովում է, որ մեր հավելվածը մնա կայուն ապագա թարմացումների ընթացքում: Մենք օգտագործում ենք Django-ի ներկառուցված `TestCase` ֆրեյմվորքը:

---

## 1. Modular Testing Areas | Մոդուլային Թեստավորման Բաժիններ

### 🇬🇧 English Explanation
Instead of one massive test function, the file is broken down into specific classes targeting isolated components:
*   **`UtilsTestCase`:** Tests purely mathematical Python logic (Pandas integrations, IQR outlier algorithms, filtering logic) entirely separate from web requests.
*   **`UploadViewTestCase`:** Simulates fake browser `POST` requests submitting `.csv`, `.xlsx`, and `.json` files. It verifies that Excel and JSON files correctly get converted into flat CSVs before database creation.
*   **`AuthViewTestCase`:** Verifies logins, invalid credentials, and confirms malicious users cannot view dashboards without authentication.
*   **`OwnershipTestCase`:** Crucial security tests. Proves that if User A attempts to `HTTP GET` or `DELETE` User B's file, Django actively intercepts the request and throws a strong `403 Forbidden` or `404 Not Found`.

### 🇦🇲 Հայերեն Բացատրություն
Փոխանակ մեկ հսկայական թեստային ֆունկցիա գրելու, ֆայլը բաժանված է կոնկրետ դասերի (classes), որոնք թիրախավորում են մեկուսացված բաղադրիչներ.
*   **`UtilsTestCase`.** Թեստավորում է զուտ մաթեմատիկական Python տրամաբանությունը (Pandas ինտեգրումներ, IQR արտասովոր տվյալների ալգորիթմներ, ֆիլտրման տրամաբանություն) ամբողջությամբ առանձնացված վեբ հարցումներից:
*   **`UploadViewTestCase`.** Սիմուլյացիա է անում կեղծ բրաուզերի `POST` հարցումներ, որոնք վերբեռնում են `.csv`, `.xlsx` և `.json` ֆայլեր: Այն ստուգում է, արդյոք Excel և JSON ֆայլերը ճիշտ կերպով փոխարկվում են CSV-ի նախքան տվյալների բազա գրանցելը:
*   **`AuthViewTestCase`.** Ստուգում է մուտքերը, սխալ գաղտնաբառերը և հաստատում, որ չգրանցված օգտատերերը չեն կարող տեսնել վահանակները առանց նույնականացման:
*   **`OwnershipTestCase`.** Անվտանգության կարևորագույն թեստեր: Ապացուցում է, որ եթե Օգտատեր Ա-ն փորձի `HTTP GET` կամ `DELETE` անել Օգտատեր Բ-ի ֆայլը, Django-ն ակտիվորեն կարգելափակի հարցումը և կվերադարձնի խիստ `403 Forbidden` (Արգելված) կամ `404 Not Found` (Չի գտնվել):

---

## 2. In-Memory Mocking Strategies | Հիշողության մեջ Mocking-ի Ռազմավարություններ

### 🇬🇧 English Explanation
When running tests, we **do not** want to create actual files on the hard drive or connect to a real Redis server (which would slow down the CI/CD pipelines significantly). 
*   **`ContentFile` Mocking:** In `_make_csv_file()`, we use `ContentFile("name,age\nBob,25".encode('utf-8'))`. This generates a virtual file directly in RAM, fooling Django into thinking an actual file was uploaded without wasting hard drive read/write cycles.
*   **Eager Celery Execution:** Using `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)`, we force asynchronous tasks to execute instantly and synchronously during testing. This allows us to assert that `ProcessedData` rows are correctly saved right after upload, without dealing with background race conditions.

### 🇦🇲 Հայերեն Բացատրություն
Թեստերը աշխատեցնելիս մենք **չենք ցանկանում** ստեղծել իրական ֆայլեր կոշտ սկավառակի վրա կամ միանալ իրական Redis սերվերին (ինչը զգալիորեն կդանդաղեցներ թեստավորման ընթացքը):
*   **`ContentFile` Mocking (Կեղծում).** `_make_csv_file()`-ում մենք օգտագործում ենք `ContentFile`: Սա ստեղծում է վիրտուալ ֆայլ անմիջապես օպերատիվ հիշողության (RAM) մեջ՝ խաբելով Django-ին, որպեսզի այն մտածի, թե իրական ֆայլ է վերբեռնվել՝ առանց կոշտ սկավառակի ռեսուրսները վատնելու:
*   **Անհապաղ (Eager) Celery Կատարում.** Օգտագործելով `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)`, մենք ստիպում ենք ասինխրոն առաջադրանքներին կատարվել ակնթարթորեն և սինխրոն (միանգամից) թեստավորման ընթացքում: Սա թույլ է տալիս մեզ համոզվել, որ `ProcessedData` տողերը ճիշտ են պահպանվել անմիջապես վերբեռնումից հետո:
