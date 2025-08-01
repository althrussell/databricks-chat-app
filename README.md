# 🧠 Databricks Chat Assistant

An enterprise-ready Streamlit app for LLM-based chat, file-assisted interaction, and cost-aware analytics — optimized for deployment on **Databricks Apps**.

---



## 🔑 Features

- 💬 Chat with model endpoints (Claude, Llama, Gemma, etc.)
- 📎 Upload and inject files (.pdf, .txt, .csv, .xlsx, .py, .md)
- 📊 Monitor usage with cost and token analytics
- 🗃️ View, load, delete, or export full conversation history
- 🔧 Manage endpoints and preferences with real-time settings

---

## 🧱 Project Structure

```
.
├── app.py                      # App entrypoint
├── app.yaml                   # Databricks app config
├── requirements.txt           # Python dependencies
├── ui/                        # UI components and pages
│   ├── styling.py, sidebar.py, main_content.py
│   └── pages/                 # Pages: chat, history, analytics, settings
├── services/                  # Business logic (models, state, parsing)
├── analytics_utils.py, db.py, auth_utils.py
└── model_serving_utils.py, conversations.py
```

---

## 🚀 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📦 Deploy on Databricks

Use the instructions in `DEPLOYMENT_GUIDE.md` to deploy as a Databricks App with proper resources and configuration.
