# 🏢 Architecture Stack Explained

Welcome to the **Analytics Website** codebase. This file explains why specific tools were adopted over others to build a robust, scalable data ingestion platform.

---

## 🐍 Backend Core (Django)
*   **The Problem:** Building APIs, managing User ORM tokens, executing Auth schemas, and connecting to Postgres securely takes hundreds of hours to write from scratch in NodeJS or Flask.
*   **The Solution:** \`Django\`. Provides an impenetrable MVC (Model-View-Template) framework with built-in CSRF protection, SQL Injection sanitization, and User Session handling instantly so developers can focus strictly on the Data Science integrations.

## 💾 Relational Database (PostgreSQL)
*   **The Problem:** Unstructured NoSQL (like MongoDB) falls apart when you need to perfectly link one \`UploadedFile\` to 500 rows of \`ProcessedData\` columns and automatically CASCADE delete all 500 rows if the file is eventually deleted.
*   **The Solution:** \`PostgreSQL\` paired with \`psycopg2\`. It offers flawless referential integrity.

## 🐼 Mathematics & Data Mapping (Pandas / NumPy)
*   **The Problem:** Normal Python `for loop` arrays iterating through a CSV of 2,000,000 rows takes roughly two whole minutes.
*   **The Solution:** `pandas` powered by `numpy`. NumPy bindings drop explicitly into C layer programming. The same 2,000,000 calculations evaluate in roughly 300 milliseconds because math is applied using advanced contiguous array vectorizations. 

## 📨 Queue Broker (Celery & Redis)
*   **The Problem:** User uploads a 50MB file. If Django begins iterating through the file to find outliers immediately, that specific user (and likely the NGINX host running the entire server) gets locked in a synchronous blocking loop for 10 seconds.
*   **The Solution:** A messaging layer (`Redis`) combined with workers (`Celery`). Django says "Hey Redis, hold this File ID." Django instantly gives the user back an HTML response "Processing in background." An idle Celery worker grabs the ID from Redis, runs the heavy code, and saves it. The core website never blocks.

---

## 🪟 Javascript & Front-End 
*   **The Problem:** Modern Users demand interactivity without seeing page flickers or full HTML re-paints.
*   **The Solution:** We combined standard HTML5 styling (`CSS3 / Bootstrap 5`) with vanilla ES6 Javascript. 
*   **The Visualization (Chart.js):** Instead of using Matplotlib (which holds an active Python memory instance open for every chart image rendered on the backend), we use simple API queries (`/api/chart_data/`) that return lightning-fast `JSON` datasets directly to the browser, allowing the client's GPU/CPU to render the canvas graphs directly using `Chart.js`.
