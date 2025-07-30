# Databricks Chat App (Streamlit) — Serving Endpoints + SQL Warehouse (no pyspark)

This build removes all pyspark usage and talks to:
- **Databricks Model Serving** for LLM calls (pay‑per‑token)
- **Databricks SQL Warehouse** (Statement Execution API via `databricks-sdk`) for Lakehouse CRUD

## What you need
- A **SQL Warehouse ID** with access to your catalog/schema/volume.
- Env vars set on the App:
  - `APP_DATABRICKS_HOST` = `https://<workspace>` (e.g., `https://e2-demo-west.cloud.databricks.com`)
  - `APP_DATABRICKS_TOKEN` = token for the App runtime identity
  - `APP_SQL_WAREHOUSE_ID` = your SQL Warehouse ID (e.g., `1234-567890-abcd123`)
  - `APP_CATALOG`, `APP_SCHEMA`, `APP_VOLUME`

## How tables are written/read
- All DDL/DML uses the **Statement Execution API** (no Spark cluster needed).
- `current_user()` is also resolved via a small SQL query to the warehouse.

## Upload ingestion
- CSV/TSV files are stored in a **per-user UC Volume** and registered as **external CSV tables** via
  ```
  CREATE TABLE <catalog>.<schema>.<auto_name>
  USING CSV OPTIONS (header true)
  LOCATION '/Volumes/<catalog>/<schema>/<volume>/<user>/uploads/<file>.csv'
  ```
- Excel files are split to per‑sheet **CSV** under `extracted/` and registered the same way.



### Warehouse by name (optional)
You can set `APP_SQL_WAREHOUSE_NAME` instead of `APP_SQL_WAREHOUSE_ID`. The app will resolve the ID at runtime.
