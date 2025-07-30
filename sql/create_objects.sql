-- You can still run these once to bootstrap in a Notebook or SQL editor:
CREATE CATALOG IF NOT EXISTS app_catalog;
USE CATALOG app_catalog;
CREATE SCHEMA IF NOT EXISTS app;
CREATE VOLUME IF NOT EXISTS app.user_files;

CREATE TABLE IF NOT EXISTS app.conversations (
  conversation_id STRING,
  user_id STRING,
  tenant_id STRING,
  title STRING,
  model STRING,
  tools ARRAY<STRING>,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  meta MAP<STRING, STRING>)
TBLPROPERTIES (delta.enableChangeDataFeed = true);

CREATE TABLE IF NOT EXISTS app.messages (
  message_id STRING,
  conversation_id STRING,
  role STRING,
  content STRING,
  tool_invocations ARRAY<STRING>,
  tokens_in INT,
  tokens_out INT,
  created_at TIMESTAMP,
  status STRING)
TBLPROPERTIES (delta.enableChangeDataFeed = true);

CREATE TABLE IF NOT EXISTS app.usage_events (
  event_id STRING,
  conversation_id STRING,
  user_id STRING,
  model STRING,
  tokens_in INT,
  tokens_out INT,
  cost DOUBLE,
  created_at TIMESTAMP,
  meta MAP<STRING, STRING>);

CREATE TABLE IF NOT EXISTS app.documents (
  doc_id STRING,
  user_id STRING,
  tenant_id STRING,
  source_type STRING,
  uc_table STRING,
  file_path STRING,
  sheet STRING,
  num_rows BIGINT,
  created_at TIMESTAMP);

CREATE TABLE IF NOT EXISTS app.theme_config (
  tenant_id STRING,
  name STRING,
  config STRING,
  updated_at TIMESTAMP);
