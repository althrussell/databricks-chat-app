# Databricks Chat App (Streamlit) — ChatGPT-like UI

A Streamlit app designed to run **natively in Databricks Apps** (per-workspace) that:

- Mimics the chatgpt.com chat UX (multi-chat sidebar, model selector, message list, chat input)
- Routes inference via **Databricks AI Gateway** (supports pay‑per‑token where configured)
- Stores **chat history in Delta** tables (Unity Catalog managed)
- Supports **per-user uploads** (CSV/Excel/Parquet) to **UC Volumes** and auto‑ingest to Delta
- Optional **RAG** via **Databricks Vector Search** (hooks provided)
- **Theming/branding** by tenant (colors/logo) loaded from UC Volumes JSON
- Deployable via **GitHub Actions** using the Databricks CLI

---

## Quick start (high-level)

1) **Create UC objects** (catalog, schema, volume, tables):
   - Open a SQL editor (or a Notebook) and run `sql/create_objects.sql`. Adjust the catalog/schema/volume names inside.

2) **Configure Databricks App (Streamlit)**:
   - App entry point: `apps/streamlit_app/app.py`
   - Environment variables (set in App configuration):
     - `APP_DATABRICKS_HOST` (e.g., https://<your-workspace-host>)
     - `APP_DATABRICKS_TOKEN` (PAT or service principal token with rights to AI Gateway, Vector Search, UC objects)
     - `APP_CATALOG` (e.g., `app_catalog`)
     - `APP_SCHEMA` (e.g., `app`)
     - `APP_VOLUME` (e.g., `user_files`)
     - Optional: `APP_TENANT_ID_DEFAULT` (fallback tenant id, e.g., `default`)
     - Optional: `APP_DEFAULT_LLM_ROUTE` (AI Gateway route for chat, e.g., `chat-dbrx`)
     - Optional: `APP_DEFAULT_EMBED_ROUTE` (AI Gateway route for embeddings, e.g., `embed-bge`)

3) **Permissions**:
   - Ensure your App *service identity* can:
     - Read/Write to the chosen UC catalog/schema/volume and Delta tables
     - Invoke **AI Gateway** routes you specify
     - Use **Vector Search** collections (if enabling RAG)

4) **Run the App**:
   - Deploy as a Databricks App (Streamlit). The sidebar exposes: chats, model selector, upload, theme.

5) **GitHub Actions**:
   - Set repository secrets: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`
   - The provided workflow will deploy the Streamlit App to your workspace using the CLI.

---

## Notes on identity & per-user storage

The app tries to resolve the **current user** primarily via Spark `SELECT current_user()`.
As a fallback, it will prompt for an identifier on first use and cache it in the session.

Per‑user storage path (example):
`/Volumes/<CAT>/<SCH>/<VOL>/<user_id>/{uploads,extracted,parquet}`

---

## RAG & Vector Search

The scaffolding includes functions to:
- Chunk & embed text/rows with an **embedding route** (AI Gateway)
- Upsert vectors into a **Vector Search collection** named by tenant/user
- Retrieve top‑k results and show citations

You must create Vector Search collections and grant access (see TODOs in code).

---

## Theming / Branding

Place a `theme.json` and optional `logo.png` under:
`/Volumes/<CAT>/<SCH>/<VOL>/branding/<tenant_id>/`

Example `theme.json`:
```json
{
  "logo_path": "/Volumes/<cat>/<sch>/<vol>/branding/<tenant_id>/logo.png",
  "colors": {
    "primary": "#0C6CF2",
    "surface": "#FFFFFF",
    "text": "#0F172A"
  },
  "radius": 12,
  "font_family": "Inter, system-ui"
}
```

---

## Disclaimer

This is a scaffold. You will likely adjust auth, permissions, and network for your environment
(e.g., Front-End PrivateLink, App service identity). Test with a non‑prod workspace first.
