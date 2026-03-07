# 🗄️ Models & Database Architecture

At the heart of any solid Django application is its database structure. This project relies entirely on Django's ORM (Object-Relational Mapper) to map Python classes directly into SQL tables. 

The two primary custom models in this system are `UploadedFile` and `ProcessedData`. Let's understand how they interact.

---

## 1. `UploadedFile` Model
This model acts as the "Parent" record. Every time a user completes a file upload, a new `UploadedFile` is instantiated.

**Key Responsibilities:**
*   **Storage Tracking:** Utilizes a `FileField` that tracks the physical location of the uploaded document inside the `uploads/` directory on the server.
*   **User Association:** Contains a `ForeignKey` linking the file securely to a specific authenticated Python `User`. If the user is anonymous, it remains `None`.
*   **State Management:** Booleans like `processed=True/False` help the frontend know if Celery has finished running mathematics on the file. If there's an error, it is stored in `error_message`.
*   **Metadata Caching:** Fields like `numeric_fields` and `categorical_fields` are cached as JSON so the application doesn't have to re-evaluate the CSV structure every time a user requests a new chart!

---

## 2. `ProcessedData` Model
This model acts as the "Child" record. It has a rigorous `ForeignKey` mapping relationship back to `UploadedFile` (`on_delete=models.CASCADE`). 

**What does it do?**
When a heavy 100,000-row CSV file is analyzed by Pandas, we don't want to scan those 100,000 rows every time we load the results page. Instead, Celery extracts statistical summaries (aggregations) and saves them as `ProcessedData` rows.

Usually, there is exactly **one `ProcessedData` row created per column** in the CSV file!

**Key Responsibilities:**
*   **Column Name Tracker:** Identifies which column this math belongs to (e.g., "Age", "Revenue").
*   **Stats JSON:** Stores mathematical derivations. E.g.: `{"mean": 45, "median": 42, "max": 120, "missing": 0}`. 
*   **Data Typer:** Categorizes columns as exactly "Numeric" or "Categorical/Object" to dictate which Charts are legally allowed to be generated for this specific dimension.

---

## ✨ Why this pattern is excellent:
1. **Database Speed:** The Web Views (`views.py`) never touch the actual CSV file. The views simply query the `ProcessedData` objects utilizing standard SQL `SELECT` queries, which return instantly.
2. **Cascade Deletions:** Because of the strict `ForeignKey` mapping, when an `UploadedFile` expires or is deleted by the user, Postgres will immediately destroy all associated `ProcessedData` automatically, securing disk space. Orphaned data is impossible.
