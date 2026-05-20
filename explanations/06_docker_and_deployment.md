# 🐳 Docker & Container Deployment | Docker և Կոնտեյներների Տեղադրում

This document explains the production-ready architecture defined in our `docker-compose.yml` and `Dockerfile`. It demonstrates how the application is isolated into scalable, independent micro-services.

Այս փաստաթուղթը բացատրում է արտադրական (production-ready) ճարտարապետությունը, որը սահմանված է մեր `docker-compose.yml` և `Dockerfile` ֆայլերում: Այն ցույց է տալիս, թե ինչպես է հավելվածը մեկուսացված (isolated) մասշտաբավորվող, անկախ միկրոսերվիսների մեջ:

---

## The Four Pillars of the Stack | Ստեկի Չորս Հիմնասյուները

Our `docker-compose.yml` spins up 4 distinct containers that talk to each other over an internal Docker network.

Մեր `docker-compose.yml`-ը միացնում է 4 հստակ կոնտեյներներ, որոնք հաղորդակցվում են միմյանց հետ Docker-ի ներքին ցանցի միջոցով:

### 1. `db` (PostgreSQL)
*   **🇬🇧 English:** Runs the official `postgres:16-alpine` image. It mounts a persistent volume `postgres_data` so that your data is not lost if the container crashes. It handles all relational data storage (`UploadedFile`, `ProcessedData`, `Users`).
*   **🇦🇲 Հայերեն:** Աշխատեցնում է պաշտոնական `postgres:16-alpine` կերպարը (image): Այն կցում է մշտական հիշողության ծավալ `postgres_data`, որպեսզի ձեր տվյալները չկորչեն, եթե կոնտեյները խափանվի: Այն կառավարում է բոլոր հարաբերական տվյալների պահպանումը:

### 2. `redis` (Message Broker)
*   **🇬🇧 English:** Runs `redis:7-alpine`. It operates purely in RAM. It acts as the "post office", holding Celery tasks (like file analysis jobs) safely in a queue until a worker is ready to take them.
*   **🇦🇲 Հայերեն:** Աշխատեցնում է `redis:7-alpine`: Այն գործում է բացառապես օպերատիվ հիշողության (RAM) մեջ: Այն ծառայում է որպես "փոստատուն"՝ անվտանգ պահելով Celery առաջադրանքները հերթում, մինչև որևէ worker պատրաստ լինի դրանք վերցնելու:

### 3. `web` (Django Application)
*   **🇬🇧 English:** Built from our custom `Dockerfile`. On startup, it automatically runs database migrations, collects static files, and binds the Gunicorn production WSGI server to port `8000`. It mounts a persistent `uploads_data` volume so user files aren't deleted on restart.
*   **🇦🇲 Հայերեն:** Կառուցված է մեր հատուկ `Dockerfile`-ից: Գործարկվելիս այն ավտոմատ կերպով կատարում է տվյալների բազայի միգրացիաները, հավաքում է ստատիկ ֆայլերը և միացնում Gunicorn արտադրական WSGI սերվերը `8000` պորտին (port): Այն նաև պահպանում է ֆայլերը `uploads_data` հատվածում:

### 4. `celery` & `celery-beat` (Background Workers)
*   **🇬🇧 English:** Uses the exact same Dockerfile as the `web` container, but executes a different startup command (`celery -A analytics_project worker`). This is brilliant because you can scale workers independently of the web server simply by running `docker-compose up --scale celery=3`.
*   **🇦🇲 Հայերեն:** Օգտագործում է ճիշտ նույն Dockerfile-ը, ինչ `web` կոնտեյները, բայց կատարում է այլ մեկնարկային հրաման (`celery -A analytics_project worker`): Սա հիանալի է, քանի որ կարող եք մեծացնել (scale) աշխատողների քանակը վեբ-սերվերից անկախ՝ պարզապես գործարկելով հրաման:

---

## Environment Variable Orchestration | Միջավայրի Փոփոխականների Կառավարում

### 🇬🇧 English Explanation
The `env_file: analytics_project/.env` directive ensures that all containers read from the same source of truth. The `web` container needs to know how to connect to the database. Instead of hardcoding `localhost`, it simply calls the Docker hostname `db` or `redis`. Docker's internal DNS resolver automatically routes `redis://redis:6379` to the correct container. 

The `depends_on` flag with `condition: service_healthy` ensures that Django waits patiently until Postgres is fully booted and accepting connections before attempting to run `.py` startup scripts.

### 🇦🇲 Հայերեն Բացատրություն
`env_file: analytics_project/.env` հրահանգը ապահովում է, որ բոլոր կոնտեյներները կարդան տվյալները միևնույն աղբյուրից: `web` կոնտեյները պետք է իմանա, թե ինչպես միանալ տվյալների բազային: Փոխարենը կոդում կոշտ (hardcode) գրելու `localhost`, այն պարզապես կանչում է Docker-ի հոսթի անունը՝ `db` կամ `redis`: Docker-ի ներքին DNS համակարգը ավտոմատ կերպով ուղղորդում է `redis://redis:6379` դեպի ճիշտ կոնտեյներ:

`depends_on` դրոշակը (flag) `condition: service_healthy` պայմանի հետ ապահովում է, որ Django-ն համբերատար սպասի մինչև Postgres-ը ամբողջությամբ միանա և ընդունի կապեր, նախքան փորձելը աշխատեցնել միգրացիոն Python սկրիպտները:
