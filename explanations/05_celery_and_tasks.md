# ⚙️ Celery Workers & Asynchronous Tasks

Data Science is computationally brutally expensive. If a massive 150MB `.CSV` file is given to Django, the synchronous parsing loop will lock the main thread, throwing Gunicorn errors, timing out NGINX, and dropping all other users from the website. 

The architecture avoids this via robust Asynchronous Job delegation.

---

## 🏎️ The Request Lifecycle Engine

### 1. The Handoff
Instead of computing the CSV the moment `views.py` receives it, the server simply performs absolute immediate validation (size checks, malicious metadata headers).
It executes `process_uploaded_file.delay(obj.id)`. This places a small, lightweight JSON descriptor string containing the Database ID of the file directly onto the **Redis Message Broker Layer**.

### 2. The Redis Broker
The Redis layer, operating entirely in-memory separately from Postgres, holds infinite "Queues". It guarantees exact-once delivery. It essentially "holds" tasks safely until an idle worker machine checks in.

### 3. The Celery Worker Node (`tasks.py`)
Operating fully detached from `views.py` (and potentially hosted on an entirely different scalable server globally), the independent Python script checks the queue stack. 

When it adopts `process_uploaded_file(file_id)`, here is the exact execution flow:

1. **Database Fetch:** Looks up the `UploadedFile` by its integer primary key.
2. **File I/O:** Opens physical file descriptors using Pandas (`pd.read_csv()`).
3. **Data Inference:** Iterates strictly over every column (inferring `data_type` logic conditionally).
4. **Calculations:** Evaluates IQR limits to spot potential outliers, calculates standard deviations, max, min, modes, and null gaps using vectorized operations (`numpy` arrays underneath) which are massively faster than raw Python loops.
5. **Database Commit:** Executes complex `bulk_create` Database commits via Django's ORM, bypassing traditional saving loop inefficiencies, storing everything exactly to `ProcessedData`. 
6. **Completion Signal:** Emits `file.processed = True` and writes `file.save()` back to Postgres.

---

## 🔄 Front-End Polling Mechanisms
When the user arrives on the `result_view()`, if `file_obj.processed` is `False`, the backend simply renders a beautiful HTML loading page ("File is still being processed"). 

Currently, users must manually refresh to see if the Celery worker has finished. 

### 💡 Future Improvements
To make this system extremely robust and modern, we could implement:
- **WebSocket Integration (Django Channels/Redis):** The frontend could subscribe to a channel. The exact millisecond Celery finishes, it sends a broadcast message to the socket, and the frontend instantly replaces the loading skeleton with the Data Table without any user reload. 
- **AJAX Long-Polling:** A simpler alternative where Javascript `setInterval()` pings an API endpoint every 3 seconds asking `is_processed=True?` and instantly reloading if configured.

Because computations happen purely off-grid, Django remains lightning-fast, reliably handling requests instantly for all active concurrent users.
