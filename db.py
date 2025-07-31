# db.py - Enhanced database module with better error handling and logging
import os
import uuid
import logging
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from databricks import sql
from databricks.sdk.core import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "1") == "1"
RUN_SQL_AS_USER = os.getenv("RUN_SQL_AS_USER", "0") == "1"
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID") or ""
CATALOG = os.getenv("CATALOG", "shared")
SCHEMA = os.getenv("SCHEMA", "app")
PRICE_PROMPT_PER_1K = float(os.getenv("PRICE_PROMPT_PER_1K", "0") or "0")
PRICE_COMPLETION_PER_1K = float(os.getenv("PRICE_COMPLETION_PER_1K", "0") or "0")

def fqn(table_name: str) -> str:
    """Generate fully qualified table name"""
    return f"{CATALOG}.{SCHEMA}.{table_name}"

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

def _get_header(name: str) -> Optional[str]:
    """Get request header from environment variables"""
    env_key = name.replace("-", "_").upper()
    return os.environ.get(env_key) or os.environ.get(name)

def get_forwarded_email() -> Optional[str]:
    """Get forwarded email from headers (legacy function for compatibility)"""
    from auth_utils import get_forwarded_email as auth_get_email
    return auth_get_email()

def get_forwarded_token() -> Optional[str]:
    """Get forwarded access token from headers (legacy function for compatibility)"""
    from auth_utils import get_forwarded_token as auth_get_token
    return auth_get_token()

def _connection_available() -> bool:
    """Check if database connection is properly configured"""
    return ENABLE_LOGGING and bool(WAREHOUSE_ID)

def _create_service_principal_connection():
    """Create connection using service principal credentials"""
    try:
        config = Config()
        return sql.connect(
            server_hostname=config.host,
            http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
            credentials_provider=lambda: config.authenticate,
        )
    except Exception as e:
        logger.error(f"Failed to create service principal connection: {e}")
        raise DatabaseError(f"Service principal connection failed: {e}")

def _create_user_connection(token: str):
    """Create connection using user access token"""
    try:
        config = Config()
        return sql.connect(
            server_hostname=config.host,
            http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
            access_token=token,
        )
    except Exception as e:
        logger.error(f"Failed to create user connection: {e}")
        raise DatabaseError(f"User connection failed: {e}")

def _get_connection_and_mode():
    """Get database connection and determine auth mode"""
    if RUN_SQL_AS_USER:
        token = get_forwarded_token()
        if token:
            try:
                return _create_user_connection(token), "user"
            except DatabaseError:
                logger.warning("User connection failed, falling back to service principal")
    
    return _create_service_principal_connection(), "app"

@contextmanager
def get_db_connection():
    """Context manager for database connections with proper cleanup"""
    if not _connection_available():
        raise DatabaseError("Database connection not available - check WAREHOUSE_ID and ENABLE_LOGGING")
    
    conn = None
    try:
        conn, mode = _get_connection_and_mode()
        logger.debug(f"Database connection established in {mode} mode")
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise DatabaseError(f"Connection error: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

def execute_sql(statement: str, params: Dict[str, Any] = None) -> None:
    """Execute SQL statement with proper error handling"""
    if not _connection_available():
        logger.warning("SQL execution skipped - database not configured")
        return
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(statement, params)
                else:
                    cursor.execute(statement)
                logger.debug(f"Executed SQL: {statement[:100]}...")
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        # Don't raise exception to prevent app crashes
        pass

def query_sql(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Execute SQL query and return results as list of dictionaries"""
    if not _connection_available():
        logger.warning("SQL query skipped - database not configured")
        return []
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert rows to dictionaries
                result = []
                for row in rows:
                    if isinstance(row, dict):
                        result.append(row)
                    else:
                        row_dict = {}
                        for i, value in enumerate(row):
                            column_name = columns[i] if i < len(columns) else f"col_{i}"
                            row_dict[column_name] = value
                        result.append(row_dict)
                
                logger.debug(f"Query returned {len(result)} rows")
                return result
                
    except Exception as e:
        logger.error(f"SQL query failed: {e}")
        return []

def fetch_single_value(query: str, params: Dict[str, Any] = None):
    """Fetch a single value from SQL query"""
    rows = query_sql(query, params)
    if rows and len(rows) > 0:
        first_row = rows[0]
        if isinstance(first_row, dict) and first_row:
            return list(first_row.values())[0]
    return None

def current_user() -> str:
    """Get current database user"""
    try:
        user = fetch_single_value("SELECT current_user() AS user")
        return user if user and user != "unknown_user" else "unknown_user"
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        return "unknown_user"

def _escape_sql_string(value: Optional[str]) -> str:
    """Escape SQL string values to prevent injection"""
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"

def ensure_conversation(
    conv_id: str, 
    user_id: str, 
    model: str, 
    title: str = "New Chat", 
    email: Optional[str] = None, 
    sql_user: Optional[str] = None
):
    """Ensure conversation exists in database with proper error handling"""
    if not _connection_available():
        return
        
    try:
        # Build metadata map
        meta_parts = []
        if email:
            meta_parts.append(f"'email', {_escape_sql_string(email)}")
        if sql_user:
            meta_parts.append(f"'sql_user', {_escape_sql_string(sql_user)}")
        
        meta_expr = f"map({', '.join(meta_parts)})" if meta_parts else "map()"
        
        # Insert or update conversation
        sql = f"""
        MERGE INTO {fqn('conversations')} AS target
        USING (
            SELECT 
                {_escape_sql_string(conv_id)} as conversation_id,
                {_escape_sql_string(user_id)} as user_id,
                'default' as tenant_id,
                {_escape_sql_string(title)} as title,
                {_escape_sql_string(model)} as model,
                ARRAY() as tools,
                current_timestamp() as created_at,
                current_timestamp() as updated_at,
                {meta_expr} as meta
        ) AS source
        ON target.conversation_id = source.conversation_id
        WHEN MATCHED THEN
            UPDATE SET updated_at = current_timestamp()
        WHEN NOT MATCHED THEN
            INSERT (conversation_id, user_id, tenant_id, title, model, tools, created_at, updated_at, meta)
            VALUES (source.conversation_id, source.user_id, source.tenant_id, source.title, source.model, source.tools, source.created_at, source.updated_at, source.meta)
        """
        
        execute_sql(sql)
        logger.info(f"Ensured conversation exists: {conv_id}")
        
    except Exception as e:
        logger.error(f"Failed to ensure conversation: {e}")

def update_conversation_model(conv_id: str, model: str):
    """Update conversation model"""
    if not _connection_available():
        return
        
    sql = f"""
    UPDATE {fqn('conversations')} 
    SET model = {_escape_sql_string(model)}, updated_at = current_timestamp() 
    WHERE conversation_id = {_escape_sql_string(conv_id)}
    """
    execute_sql(sql)
    logger.debug(f"Updated conversation model: {conv_id} -> {model}")

def update_conversation_title(conv_id: str, new_title: str):
    """Update conversation title"""
    if not _connection_available():
        return
        
    sql = f"""
    UPDATE {fqn('conversations')} 
    SET title = {_escape_sql_string(new_title)}, updated_at = current_timestamp() 
    WHERE conversation_id = {_escape_sql_string(conv_id)}
    """
    execute_sql(sql)
    logger.debug(f"Updated conversation title: {conv_id} -> {new_title}")

def log_message(
    conv_id: str, 
    role: str, 
    content: str, 
    tokens_in: int = 0, 
    tokens_out: int = 0, 
    status: str = "ok"
):
    """Log a message to the database"""
    if not _connection_available():
        return
        
    message_id = str(uuid.uuid4())
    sql = f"""
    INSERT INTO {fqn('messages')} 
    (message_id, conversation_id, role, content, tool_invocations, tokens_in, tokens_out, created_at, status)
    VALUES (
        {_escape_sql_string(message_id)},
        {_escape_sql_string(conv_id)},
        {_escape_sql_string(role)},
        {_escape_sql_string(content)},
        ARRAY(),
        {tokens_in},
        {tokens_out},
        current_timestamp(),
        {_escape_sql_string(status)}
    )
    """
    execute_sql(sql)
    logger.debug(f"Logged message: {role} in {conv_id}")

def log_usage(
    conv_id: str, 
    user_id: str, 
    model: str, 
    tokens_in: int, 
    tokens_out: int, 
    email: Optional[str] = None, 
    sql_user: Optional[str] = None
):
    """Log usage metrics to the database"""
    if not _connection_available():
        return
        
    try:
        # Calculate cost
        cost = (tokens_in / 1000.0) * PRICE_PROMPT_PER_1K + (tokens_out / 1000.0) * PRICE_COMPLETION_PER_1K
        
        # Build metadata
        meta_parts = []
        if email:
            meta_parts.append(f"'email', {_escape_sql_string(email)}")
        if sql_user:
            meta_parts.append(f"'sql_user', {_escape_sql_string(sql_user)}")
        
        meta_expr = f"map({', '.join(meta_parts)})" if meta_parts else "map()"
        
        event_id = str(uuid.uuid4())
        sql = f"""
        INSERT INTO {fqn('usage_events')} 
        (event_id, conversation_id, user_id, model, tokens_in, tokens_out, cost, created_at, meta)
        VALUES (
            {_escape_sql_string(event_id)},
            {_escape_sql_string(conv_id)},
            {_escape_sql_string(user_id)},
            {_escape_sql_string(model)},
            {tokens_in},
            {tokens_out},
            {cost},
            current_timestamp(),
            {meta_expr}
        )
        """
        execute_sql(sql)
        logger.debug(f"Logged usage: {tokens_in}+{tokens_out} tokens, ${cost:.4f}")
        
    except Exception as e:
        logger.error(f"Failed to log usage: {e}")

def list_conversations(
    user_id: Optional[str], 
    search: str = "", 
    limit: int = 100, 
    include_content: bool = False
) -> List[Dict[str, Any]]:
    """List conversations for a user with search functionality"""
    if not _connection_available():
        return []
    
    try:
        # Build WHERE clause
        where_conditions = ["1=1"]
        
        if user_id:
            where_conditions.append(f"c.user_id = {_escape_sql_string(user_id)}")
        
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            search_conditions = [
                f"c.title ILIKE {_escape_sql_string(search_term)}",
                f"c.model ILIKE {_escape_sql_string(search_term)}"
            ]
            
            if include_content:
                search_conditions.append(f"""
                EXISTS (
                    SELECT 1 FROM {fqn('messages')} m 
                    WHERE m.conversation_id = c.conversation_id 
                    AND m.content ILIKE {_escape_sql_string(search_term)}
                )
                """)
            
            where_conditions.append(f"({' OR '.join(search_conditions)})")
        
        where_clause = " AND ".join(where_conditions)
        
        # Main query
        query = f"""
        SELECT 
            c.conversation_id,
            c.title,
            c.model,
            c.created_at,
            c.updated_at,
            COALESCE(msg_stats.message_count, 0) AS messages,
            COALESCE(usage_stats.tokens_in, 0) AS tokens_in,
            COALESCE(usage_stats.tokens_out, 0) AS tokens_out,
            COALESCE(usage_stats.cost, 0.0) AS cost
        FROM {fqn('conversations')} c
        LEFT JOIN (
            SELECT 
                conversation_id,
                COUNT(*) AS message_count
            FROM {fqn('messages')}
            GROUP BY conversation_id
        ) msg_stats ON c.conversation_id = msg_stats.conversation_id
        LEFT JOIN (
            SELECT 
                conversation_id,
                SUM(tokens_in) AS tokens_in,
                SUM(tokens_out) AS tokens_out,
                SUM(cost) AS cost
            FROM {fqn('usage_events')}
            GROUP BY conversation_id
        ) usage_stats ON c.conversation_id = usage_stats.conversation_id
        WHERE {where_clause}
        ORDER BY c.updated_at DESC
        LIMIT {int(limit)}
        """
        
        return query_sql(query)
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        return []

def fetch_conversation_messages(conv_id: str) -> List[Dict[str, Any]]:
    """Fetch messages for a conversation"""
    if not _connection_available():
        return []
    
    query = f"""
    SELECT role, content, created_at, tokens_in, tokens_out, status
    FROM {fqn('messages')}
    WHERE conversation_id = {_escape_sql_string(conv_id)}
    ORDER BY created_at ASC
    """
    
    return query_sql(query)

def fetch_conversation_meta(conv_id: str) -> Dict[str, Any]:
    """Fetch conversation metadata"""
    if not _connection_available():
        return {}
    
    query = f"""
    SELECT conversation_id, title, model, created_at, updated_at, user_id, meta
    FROM {fqn('conversations')}
    WHERE conversation_id = {_escape_sql_string(conv_id)}
    LIMIT 1
    """
    
    results = query_sql(query)
    return results[0] if results else {}

def delete_conversation(conv_id: str):
    """Delete a conversation and all related data"""
    if not _connection_available():
        return
    
    try:
        # Delete in order due to foreign key constraints
        execute_sql(f"DELETE FROM {fqn('usage_events')} WHERE conversation_id = {_escape_sql_string(conv_id)}")
        execute_sql(f"DELETE FROM {fqn('messages')} WHERE conversation_id = {_escape_sql_string(conv_id)}")
        execute_sql(f"DELETE FROM {fqn('conversations')} WHERE conversation_id = {_escape_sql_string(conv_id)}")
        
        logger.info(f"Deleted conversation: {conv_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete conversation {conv_id}: {e}")

def usage_summary(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get usage summary for analytics"""
    if not _connection_available():
        return {"totals": {}, "by_day": [], "by_model": []}
    
    try:
        # Build user filter
        user_filter = f"WHERE user_id = {_escape_sql_string(user_id)}" if user_id else ""
        
        # Get totals
        totals_query = f"""
        SELECT 
            COUNT(DISTINCT conversation_id) as conversations,
            COUNT(*) as events,
            SUM(tokens_in) as tokens_in,
            SUM(tokens_out) as tokens_out,
            SUM(cost) as cost
        FROM {fqn('usage_events')}
        {user_filter}
        """
        
        totals_result = query_sql(totals_query)
        totals = totals_result[0] if totals_result else {}
        
        # Get daily breakdown
        daily_query = f"""
        SELECT 
            DATE(created_at) as day,
            SUM(tokens_in) as tokens_in,
            SUM(tokens_out) as tokens_out,
            SUM(cost) as cost,
            COUNT(*) as events
        FROM {fqn('usage_events')}
        {user_filter}
        GROUP BY DATE(created_at)
        ORDER BY day DESC
        LIMIT 30
        """
        
        by_day = query_sql(daily_query)
        
        # Get model breakdown
        model_query = f"""
        SELECT 
            model,
            SUM(tokens_in + tokens_out) as tokens,
            SUM(cost) as cost,
            COUNT(*) as events
        FROM {fqn('usage_events')}
        {user_filter}
        GROUP BY model
        ORDER BY cost DESC
        LIMIT 20
        """
        
        by_model = query_sql(model_query)
        
        return {
            "totals": totals,
            "by_day": by_day,
            "by_model": by_model
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage summary: {e}")
        return {"totals": {}, "by_day": [], "by_model": []}

def test_connection() -> Dict[str, Any]:
    """Test database connection and return status"""
    if not _connection_available():
        return {
            "success": False,
            "error": "Database not configured",
            "details": "WAREHOUSE_ID or ENABLE_LOGGING not set"
        }
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
                if result:
                    return {
                        "success": True,
                        "message": "Database connection successful",
                        "user": current_user()
                    }
                else:
                    return {
                        "success": False,
                        "error": "No result from test query"
                    }
                    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "details": "Connection test failed"
        }