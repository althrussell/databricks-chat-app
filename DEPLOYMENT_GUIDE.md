# 🚀 Databricks Chat App Deployment Guide

This guide will walk you through deploying the LLM Chat Assistant on **Databricks Apps** using either ClickOps or the Databricks CLI.

---

## ✅ Prerequisites

- A Databricks workspace with:
  - Repos access
  - Apps support
  - SQL Warehouse
  - Model Serving endpoints

---

## 📁 Folder Requirements

Your repo should contain:

- `app.py` – Streamlit entry point
- `app.yaml` – Deployment config
- `requirements.txt` – Python libs
- `ui/`, `services/`, etc. – Full code structure

---

## ⚙️ Environment Variables

Set these in your App Environment settings:

```env
DATABRICKS_WAREHOUSE_ID=<your_sql_warehouse_id>
CATALOG=shared
SCHEMA=app
```

---

## 📘 Resources Required

| Type              | Key                 | Permissions |
|-------------------|---------------------|-------------|
| SQL Warehouse     | Shared Endpoint     | Can Use     |
| Serving Endpoint  | databricks-claude-sonnet-4 | Can Query |
| Serving Endpoint  | databricks-llama-4-maverick | Can Query |
| Serving Endpoint  | databricks-gemma-3-12b | Can Query |

These must be configured under **App > Settings > Resources**.

---

## 🏗️ Deploying with CLI

See `databricks_cli_instructions.md`.

## 🖱️ Deploying with UI

See `databricks_clickops_instructions.md`.
