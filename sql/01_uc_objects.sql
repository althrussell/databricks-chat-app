-- Databricks Chat App: UC Objects (adjust catalog/schema as needed)
-- Assumes CATALOG=shared, SCHEMA=app (defaults used by the app).
USE CATALOG shared;
CREATE SCHEMA IF NOT EXISTS app;

-- Volume for user files (uploads, exports, branding)
CREATE VOLUME IF NOT EXISTS app.user_files;

-- Conversations table
CREATE TABLE IF NOT EXISTS app.conversations (
  conversation_id STRING,
  user_id STRING,
  tenant_id STRING,
  title STRING,
  model STRING,
  tools ARRAY<STRING>,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  meta MAP<STRING, STRING>
)
TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- Messages table
CREATE TABLE IF NOT EXISTS app.messages (
  message_id STRING,
  conversation_id STRING,
  role STRING,              -- user | assistant | system | tool
  content STRING,
  tool_invocations ARRAY<STRING>,
  tokens_in INT,
  tokens_out INT,
  created_at TIMESTAMP,
  status STRING
)
TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- Usage events for cost/billing dashboards
CREATE TABLE IF NOT EXISTS app.usage_events (
  event_id STRING,
  conversation_id STRING,
  user_id STRING,
  model STRING,
  tokens_in INT,
  tokens_out INT,
  cost DOUBLE,
  created_at TIMESTAMP,
  meta MAP<STRING, STRING>
);

-- Document registry (for future uploads feature)
CREATE TABLE IF NOT EXISTS app.documents (
  doc_id STRING,
  user_id STRING,
  tenant_id STRING,
  source_type STRING,       -- csv | excel | parquet | txt | pdf (extensible)
  uc_table STRING,
  file_path STRING,
  sheet STRING,
  num_rows BIGINT,
  created_at TIMESTAMP
);

-- Theme configuration (optional; or store as JSON files in Volume)
CREATE TABLE IF NOT EXISTS app.theme_config (
  tenant_id STRING,
  name STRING,
  config STRING,            -- JSON string
  updated_at TIMESTAMP
);
