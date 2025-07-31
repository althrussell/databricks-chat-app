# 📦 Databricks CLI Deployment Instructions

## 1. Install CLI

```bash
pip install databricks-cli
databricks configure --token
```

## 2. Upload Repo

```bash
databricks repos create --url <repo-url> --provider gitHub
```

Or sync with:
```bash
databricks repos update --path /Repos/user/project --branch main
```

## 3. Deploy App

Create a new app via CLI (if supported) or continue in ClickOps.

## 4. Set Environment Variables

```bash
databricks workspace import app.yaml /Apps/chat-assistant/app.yaml --overwrite
```

Then define env vars manually or via UI.
