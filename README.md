# Databricks Chat App (Streamlit) — Serving Endpoints Only

A Streamlit app designed to run **natively in Databricks Apps** (per-workspace) that:

- Mimics the chatgpt.com chat UX (multi-chat sidebar, model selector, message list, chat input)
- Talks **directly to Databricks Model Serving Endpoints** (pay‑per‑token); **no AI Gateway required**
- Stores **chat history in Delta** tables (Unity Catalog managed)
- Supports **per-user uploads** (CSV/Excel/Parquet) to **UC Volumes** and auto‑ingest to Delta
- Optional **RAG** hooks (Vector Search wiring points are provided)
- **Theming/branding** by tenant (colors/logo) from JSON in UC Volumes
- Deploy via **Databricks Repos** or **CLI import-dir** (no GitHub Actions needed)

---

## Quick start

1) **Create UC objects**: open a SQL editor and run `sql/create_objects.sql`. Adjust catalog/schema/volume names.
2) **Create (or confirm) Serving Endpoints** you want to allow (e.g. `databricks-claude-sonnet-4`, `databricks-dbrx-instruct`).
3) (Optional) Edit **`inference/model_catalog.yaml`** to list endpoints and metadata.
4) Edit **`config/app_config.yaml`** → set `allowed_model_ids` to control which appear in the UI dropdown.
5) Create a **Databricks App (Streamlit)** with entry point `apps/streamlit_app/app.py`, set ENV vars, add Python packages, run.

### Environment variables for the App
- `APP_DATABRICKS_HOST` = `https://<your-workspace-host>` (e.g., `https://e2-demo-west.cloud.databricks.com`)
- `APP_DATABRICKS_TOKEN` = PAT/SPN token for the App runtime (must have Can Query on endpoints + UC rights)
- `APP_CATALOG` = e.g., `app_catalog`
- `APP_SCHEMA`  = `app`
- `APP_VOLUME`  = `user_files`

### Python packages (App config → Python packages)
```
streamlit
pandas
openpyxl
pyarrow
requests
pyyaml
databricks-sdk
databricks-vectorsearch
```

---

## Model selection & allow-listing

- `inference/model_catalog.yaml` defines **all** models/endpoints known to the app.
- `config/app_config.yaml` → `allowed_model_ids: [...]` limits which appear in the **UI dropdown**.
  If `allowed_model_ids` is empty or omitted, the UI shows only entries with `allowed: true` in `model_catalog.yaml`.

Example (allow just Claude Sonnet 4):
```yaml
app:
  allowed_model_ids: ["sonnet-4"]
```

---

## Serving payloads

By default, the app sends **OpenAI‑style chat** payloads to Databricks Serving:
```json
{ "messages": [...], "max_tokens": 768, "temperature": 0.2 }
```
If you host a custom pipeline that expects a different schema, set the model `schema` field to `anthropic` or `raw` and adjust `raw_template`
in `inference/model_catalog.yaml` for that model (see comments in that file).

---

## e2-demo-west example

To use the built-in **Claude Sonnet 4** endpoint:
- Ensure an endpoint named `databricks-claude-sonnet-4` exists and your App identity has **Can Query**.
- Set `APP_DATABRICKS_HOST=https://e2-demo-west.cloud.databricks.com`
- In `config/app_config.yaml`, set `allowed_model_ids: ["sonnet-4"]`.
- Launch the App and pick **Claude Sonnet 4** in the dropdown.
