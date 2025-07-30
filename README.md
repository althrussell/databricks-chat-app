# Databricks Chat App — App-Local Modules (Serving + SQL Warehouse, no pyspark)

This build keeps **all runtime Python modules and config under the entrypoint directory** so that
Databricks Apps packages everything needed. No `PYTHONPATH` tweaks required.

**Entry point:** `apps/streamlit_app/app.py`

**What changed vs prior build**
- Moved `inference/`, `pipelines/`, and `config/app_config.yaml` **under** `apps/streamlit_app/`.
- Added `__init__.py` so imports like `from inference.rag import ...` work relative to the entrypoint.
- Still uses **Databricks Model Serving** for LLM and **SQL Warehouse** (Statement Execution API) for tables.

**Environment variables required**
- `APP_DATABRICKS_HOST` = `https://<workspace>`
- `APP_DATABRICKS_TOKEN` = token for the App identity
- `APP_CATALOG`, `APP_SCHEMA`, `APP_VOLUME`
- **Either** `APP_SQL_WAREHOUSE_ID` **or** `APP_SQL_WAREHOUSE_NAME`

**Python packages**
See `apps/streamlit_app/requirements.txt` (install these in the App UI).

**SQL bootstrap**
Still available under `sql/create_objects.sql` to create catalog/schema/tables/volume once.
