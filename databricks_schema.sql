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

-- Volume for file storage (optional future enhancement)
CREATE VOLUME IF NOT EXISTS shared.app.uploads;
