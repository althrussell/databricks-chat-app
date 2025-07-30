-- Databricks AI Chat Assistant Database Schema Setup
-- Run these SQL commands in your Databricks workspace to set up the required tables

-- Set your catalog and schema (adjust as needed)
USE CATALOG shared;
USE SCHEMA app;

-- Create the volume for file storage (if it doesn't exist)
CREATE VOLUME IF NOT EXISTS chat_files
COMMENT 'Storage volume for chat application file uploads';

-- Create conversations table with liquid clustering
CREATE OR REPLACE TABLE conversations (
    conversation_id STRING NOT NULL,
    user_id STRING NOT NULL,
    tenant_id STRING,
    title STRING,
    model STRING NOT NULL,
    tools ARRAY<STRING>,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    meta MAP<STRING, STRING>
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
)
COMMENT 'Chat conversations metadata';

-- Create messages table with liquid clustering
CREATE OR REPLACE TABLE messages (
    message_id STRING NOT NULL,
    conversation_id STRING NOT NULL,
    role STRING NOT NULL,
    content STRING NOT NULL,
    tool_invocations ARRAY<STRING>,
    tokens_in INT,
    tokens_out INT,
    created_at TIMESTAMP,
    status STRING
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
)
COMMENT 'Individual chat messages';

-- Create usage_events table for analytics with liquid clustering
CREATE OR REPLACE TABLE usage_events (
    event_id STRING NOT NULL,
    conversation_id STRING NOT NULL,
    user_id STRING NOT NULL,
    model STRING NOT NULL,
    tokens_in INT,
    tokens_out INT,
    cost DOUBLE,
    created_at TIMESTAMP,
    meta MAP<STRING, STRING>
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.enableChangeDataFeed' = 'true'
)
COMMENT 'Token usage and cost tracking';

-- Create message_reactions table for user feedback with liquid clustering
CREATE OR REPLACE TABLE message_reactions (
    message_id STRING NOT NULL,
    user_id STRING NOT NULL,
    reaction_type STRING NOT NULL,
    created_at TIMESTAMP
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'User reactions to assistant messages';

-- Create message_files table for file attachments with liquid clustering
CREATE OR REPLACE TABLE message_files (
    message_id STRING NOT NULL,
    file_path STRING NOT NULL,
    filename STRING NOT NULL,
    file_size BIGINT,
    content_type STRING,
    created_at TIMESTAMP
)
USING DELTA
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'File attachments linked to messages';

-- Optimize tables for better performance
OPTIMIZE conversations;
OPTIMIZE messages;
OPTIMIZE usage_events;
OPTIMIZE message_reactions;
OPTIMIZE message_files;

-- Grant appropriate permissions (adjust as needed for your workspace)
-- Replace 'your-service-principal' and 'your-user-group' with actual names

-- Example service principal grants:
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE conversations TO `your-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE messages TO `your-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE usage_events TO `your-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE message_reactions TO `your-service-principal`;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE message_files TO `your-service-principal`;

-- Example user group grants:
-- GRANT SELECT ON TABLE conversations TO `your-user-group`;
-- GRANT SELECT ON TABLE messages TO `your-user-group`;
-- GRANT SELECT ON TABLE usage_events TO `your-user-group`;

-- Grant volume permissions
-- GRANT READ FILES, WRITE FILES ON VOLUME chat_files TO `your-service-principal`;
-- GRANT READ FILES ON VOLUME chat_files TO `your-user-group`;

-- Create some useful views for analytics
CREATE OR REPLACE VIEW conversation_stats AS
SELECT 
    user_id,
    COUNT(DISTINCT conversation_id) as total_conversations,
    COUNT(DISTINCT DATE(created_at)) as active_days,
    MIN(created_at) as first_conversation,
    MAX(updated_at) as last_activity
FROM conversations
GROUP BY user_id;

CREATE OR REPLACE VIEW daily_usage_summary AS
SELECT 
    DATE(u.created_at) as usage_date,
    u.user_id,
    u.model,
    COUNT(*) as total_requests,
    SUM(u.tokens_in) as total_input_tokens,
    SUM(u.tokens_out) as total_output_tokens,
    SUM(u.cost) as total_cost
FROM usage_events u
GROUP BY DATE(u.created_at), u.user_id, u.model
ORDER BY usage_date DESC, total_requests DESC;

CREATE OR REPLACE VIEW popular_models AS
SELECT 
    model,
    COUNT(DISTINCT conversation_id) as conversations_count,
    COUNT(DISTINCT user_id) as unique_users,
    SUM(tokens_in) as total_input_tokens,
    SUM(tokens_out) as total_output_tokens,
    AVG(cost) as avg_cost_per_request
FROM usage_events
WHERE created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY model
ORDER BY conversations_count DESC;

-- Verify tables were created successfully
SHOW TABLES;

-- Display table schemas
DESCRIBE conversations;
DESCRIBE messages;
DESCRIBE usage_events;
DESCRIBE message_reactions;
DESCRIBE message_files;

-- Show clustering information
DESCRIBE DETAIL conversations;
DESCRIBE DETAIL messages;

-- Sample queries to test the setup
SELECT 'Schema setup completed successfully' as status;

-- Test volume access (this will create a test file)
-- Note: Uncomment this if you want to test volume access
-- PUT 'SELECT "test" as message' INTO '/Volumes/shared/app/chat_files/test.txt';

SHOW VOLUMES;

-- Display sample analytics views
SELECT * FROM conversation_stats LIMIT 5;
SELECT * FROM daily_usage_summary LIMIT 5;
SELECT * FROM popular_models LIMIT 5;