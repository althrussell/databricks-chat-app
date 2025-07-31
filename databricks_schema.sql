-- SQL setup for LLM Chat App

CREATE CATALOG IF NOT EXISTS shared;
CREATE SCHEMA IF NOT EXISTS shared.app;

-- Table to store chat history
CREATE TABLE IF NOT EXISTS shared.app.conversations (
    conversation_id STRING,
    title STRING,
    created_at TIMESTAMP,
    model STRING,
    cost DOUBLE,
    messages INT
)
CLUSTER BY AUTO;

-- Table to store message logs
CREATE TABLE IF NOT EXISTS shared.app.messages (
    conversation_id STRING,
    message_index INT,
    role STRING,
    content STRING,
    timestamp TIMESTAMP
)
CLUSTER BY AUTO;

CREATE TABLE IF NOT EXISTS shared.app.usage_events (
  event_id STRING NOT NULL,
  conversation_id STRING NOT NULL,
  user_id STRING NOT NULL,
  model STRING,
  tokens_in INT,
  tokens_out INT,
  cost DOUBLE,
  created_at TIMESTAMP,
  meta MAP<STRING, STRING>
)
COMMENT 'Usage logging per prompt+response'
CLUSTER BY AUTO;

CREATE TABLE IF NOT EXISTS shared.app.titles (
  conversation_id STRING NOT NULL,
  title STRING,
  created_at TIMESTAMP
)
COMMENT 'Stores generated or user-defined titles for conversations'
CLUSTER BY AUTO;


-- Volume for file storage (optional future enhancement)
CREATE VOLUME IF NOT EXISTS shared.app.uploads;
