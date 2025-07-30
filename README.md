# Databricks Chat App (Stable)

A minimal, production-friendly **Databricks App** that mimics ChatGPT-style chat for **Databricks pay-per-token models**, with:
- **Model dropdown** (config-driven) — no AI Gateway required
- **Chat history** that **persists** across model changes
- **Robust serving calls** (sliding context window, serve-first-then-log)
- **Usage & chat logging** to Unity Catalog tables
- Optional **OBO** mode to run SQL **as the signed-in user**
- Optional **email capture** from `X-Forwarded-Email` and stored in `meta`

## Repo layout

```
app/
  app.py
  app.yaml
  model_serving_utils.py
  requirements.txt
sql/
  01_uc_objects.sql
  02_verify.sql
  03_grants_examples.sql
```

## Prereqs

- Databricks workspace with **Databricks Apps (Public Preview/GA)** enabled.
- A **SQL Warehouse** (ID available, e.g., `75fd8278393d07eb`).
- At least one **Serving Endpoint** for a Databricks-hosted model (e.g., `databricks-claude-sonnet-4`).

## Deploy (Databricks Apps)

1. **Import this repo** into your workspace (Repos or Workspace files).
2. Open **Create App** → **Source**: point to `/app` → **Entry point**: `app.py`.
3. In **Python Packages**, paste the contents of `app/requirements.txt`.
4. Ensure the app picks up **`app/app.yaml`** (command & env). If your environment panel is read-only, `app.yaml` is used by the app runtime.
5. **Resources/Permissions**:
   - App identity (or end users, if OBO) must **Can Query** each Serving Endpoint you list.
   - App identity (or end users, if OBO) must **CAN USE** the SQL Warehouse.
   - For logging, grant **INSERT/UPDATE** on `shared.app.*` (see `sql/03_grants_examples.sql`).

## Configure models

Edit `app/app.yaml`:

```yaml
- name: SERVING_ENDPOINT
  value: "databricks-claude-sonnet-4"         # default preselected model
- name: SERVING_ENDPOINTS_CSV
  value: "endpoint|Label,endpoint2|Label2"    # dropdown list
```

**Example** (included by default):

```
databricks-claude-sonnet-4|Claude Sonnet 4,
databricks-llama-4-maverick|Llama 4 Maverick,
databricks-gemma-3-12b|Gemma 3 12B
```

## Create UC objects

Run `sql/01_uc_objects.sql` (adjust catalog/schema if needed). Default is `shared.app`.

Then verify after sending a message:

```
sql/02_verify.sql
```

## Email logging & OBO

- If your Apps environment forwards user headers, we capture **`X-Forwarded-Email`** and store it in the `meta` map, and use it as `user_id` when available.
- To run SQL as the end user (OBO), set:
  ```yaml
  - name: RUN_SQL_AS_USER
    value: "1"
  ```
  The app tries `X-Forwarded-Access-Token`; if missing/invalid, it **falls back** to the app identity.

## Sliding context window

Set the number of messages passed to the model each turn:

```yaml
- name: MAX_TURNS
  value: "12"
```

Lower values reduce token usage and improve reliability during long conversations; increase if you need more context.

## Cost logging (optional)

Set the token pricing in `app.yaml` to compute `cost` in `usage_events`:

```yaml
- name: PRICE_PROMPT_PER_1K
  value: "0"
- name: PRICE_COMPLETION_PER_1K
  value: "0"
```

## Troubleshooting

- **Chat works but no rows in tables**
  - Confirm `ENABLE_LOGGING=1` and app identity (or user in OBO) has INSERT/UPDATE on `shared.app.*`.
  - Check the sidebar identity line (shows email/sql_user and SQL auth mode).

- **OAuth localhost port errors**
  - This app uses a non-interactive token provider for the App identity; those errors should be gone.
  - If you see `X-Forwarded-Access-Token` issues, set `RUN_SQL_AS_USER=0` to force App identity.

- **Model switch does nothing**
  - Watch the banner “Calling endpoint: <id>” before each request. Use the “Test selected endpoint” button.

## License

MIT — see `LICENSE`.

## Roadmap / Optional features to add

- Uploads → UC Volume → External Tables + `app.documents`
- Admin read-only view for conversations/messages
- Per-tenant branding via `app.theme_config`
- Export/fork conversations
