# 🖱️ ClickOps Deployment Instructions

## 1. Upload Repo

- Go to **Workspace > Repos**
- Add a new Repo from GitHub or upload manually

## 2. Open `app.yaml` and verify:

```yaml
entrypoint: app.py
libraries:
  - streamlit
  - pandas
  - openpyxl
  - PyMuPDF
permissions:
  - allow: all
    level: CAN_RUN
```

## 3. Create App

- Go to **Workspace > Apps > Create App**
- Select this repo and `app.py`
- Assign required serving endpoints and SQL warehouse
- Add these environment variables:

```env
DATABRICKS_WAREHOUSE_ID=...
CATALOG=shared
SCHEMA=app
```

## 4. Click **Deploy**
