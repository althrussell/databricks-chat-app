-- Verify logging after sending a message in the app
USE CATALOG shared;

SELECT conversation_id, user_id, model, meta['email'] AS email, meta['sql_user'] AS sql_user, updated_at
FROM app.conversations
ORDER BY updated_at DESC
LIMIT 20;

SELECT role, substr(content,1,120) AS content_snip, tokens_in, tokens_out, created_at
FROM app.messages
ORDER BY created_at DESC
LIMIT 20;

SELECT user_id, meta['email'] AS email, meta['sql_user'] AS sql_user, model, tokens_in, tokens_out, cost, created_at
FROM app.usage_events
ORDER BY created_at DESC
LIMIT 20;
