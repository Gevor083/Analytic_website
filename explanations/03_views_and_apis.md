# 📂 Core Backend Logic: `analytics_app/views.py`

When working with data-heavy applications, keeping views thin and logic separate makes a huge difference.

## Fat Views vs. Thin Views (The Golden Rule)

In Django, `views.py` is simply a traffic controller. A request comes in via an HTTP method (GET, POST), and the view should **only** be responsible for routing that request, triggering a function, checking authentication, and returning an HTTP Response. 

**Anti-Pattern:** Fat Views contain 2,000 lines of data science code, DataFrame operations, API calls, error catches, file processing chunks, and raw SQL queries grouped together. This is impossible to test, debug, or read.

**Modern Architecture:** Thin views simply map incoming requests to dedicated files like `services.py` or `.delay()` tasks. 

---

## 🛠 Active API Endpoints

We upgraded the application from a multi-page routing framework to a single-page interactive app (SPA) using **JSON APIs** instead of heavy HTML template responses. 

### 1. `chart_data_api(request, file_id)`
This is the single most important view in the app! 
*   **Method:** HTTP GET
*   **How it works:** Expects query parameters (`?chart_type=pie&x_axis=Department`).
*   **The Backend Logic:** It queries the database, extracts a tiny targeted subset of the required Pandas DataFrame (`df[x_axis]`), sanitizes `NaN` objects (because JSON syntax crashes if it receives a `None` float type), and wraps it cleanly into a JSON object `{"labels": [...], "data": [...]}`.
*   **Why?** This prevents Matplotlib from destroying server RAM and allows `Chart.js` to animate interactive charts gracefully on the user's computer via `fetch()`.

### 2. `set_theme(request)`
Handles our Dark/Light Mode state! 
*   **Method:** HTTP POST
*   **Security:** Mandates `X-CSRFToken` in the headers. 
*   **How it works:** It extracts the user's preference payload from the Javascript `fetch` body, then permanently writes `request.session['theme'] = 'dark'`. 
*   **The Power:** Because Django controls the initial HTML render, every subsequent page the user loads will naturally, instantly, and natively load dark-mode CSS classes from the first millisecond because of our Context Processors synchronizing with this API!

---

## 🛑 Validation and Upload Restrictions

The `upload_view()` is heavily guarded because File I/O operations are the #1 source of server hacks. 

1. **Size Enforcement:** `if uploaded_file.size > settings.MAX_UPLOAD_SIZE:` immediately throws out files exceeding 30MB without passing them to memory or Pandas to prevent buffer-overflow DDoS attacks.
2. **Type Enforcement:** Only permits strict whitelists of `.csv`, `.json`, and `.xlsx`. 
3. **Data Uniformity Conversion:** If an Excel document (`.xlsx`) or JSON dictionary (`.json`) slips through, the code executes an incredibly clever in-memory conversion block utilizing `io.StringIO()`. It maps every single schema back to a standardized flat CSV buffer, saving the exact CSV directly to the filesystem before uploading. This drastically simplifies Celery tasks because the worker node only ever has to know how to process a CSV!
