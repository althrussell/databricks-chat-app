# auth_utils.py - Enhanced authentication utilities with proper header handling
import os
import streamlit as st
from typing import Optional, Dict, Any

def setup_request_context():
    """
    Safely extract forwarded headers from the environment and store them in session state.
    This prevents overwriting valid values and ensures the earliest valid source is used.
    """
    if "auth_headers" not in st.session_state:
        st.session_state.auth_headers = {}

    # Define canonical keys and all header variants
    header_map = {
        "email": [
            "X_FORWARDED_EMAIL", "HTTP_X_FORWARDED_EMAIL",
            "DATABRICKS_FORWARD_EMAIL", "USER_EMAIL", "DB_USER_EMAIL"
        ],
        "access_token": [
            "X_FORWARDED_ACCESS_TOKEN", "HTTP_X_FORWARDED_ACCESS_TOKEN",
            "DATABRICKS_FORWARD_ACCESS_TOKEN", "ACCESS_TOKEN"
        ],
        "user": [
            "X_FORWARDED_USER", "HTTP_X_FORWARDED_USER",
            "DATABRICKS_FORWARD_USER", "FORWARDED_USER", "USER_ID", "USERNAME"
        ]
    }

    for canonical_key, header_variants in header_map.items():
        for var in header_variants:
            val = os.environ.get(var)
            if val and val.strip():
                # Save the first found valid value only
                if canonical_key not in st.session_state.auth_headers:
                    st.session_state.auth_headers[canonical_key] = val.strip()
                break  # stop checking once we have a value



def get_forwarded_email() -> Optional[str]:
    """
    Get the forwarded email from various possible sources.
    This function checks multiple environment variables that might contain the user's email.
    """
    # Check session state first (from setup_request_context)
    if hasattr(st.session_state, 'auth_headers') and 'email' in st.session_state.auth_headers:
        return st.session_state.auth_headers['email']
    
    # Check environment variables in order of preference
    email_env_vars = [
        "HTTP_X_FORWARDED_EMAIL",
        "X_FORWARDED_EMAIL", 
        "X-FORWARDED-EMAIL",
        "DATABRICKS_FORWARD_EMAIL",
        "FORWARDED_EMAIL",
        "USER_EMAIL",
        # Databricks-specific variables
        "DB_USER_EMAIL",
        "DATABRICKS_USER_EMAIL"
    ]
    
    for env_var in email_env_vars:
        email = os.environ.get(env_var)
        if email and email.strip():
            # Cache in session state for future use
            if not hasattr(st.session_state, 'auth_headers'):
                st.session_state.auth_headers = {}
            st.session_state.auth_headers['email'] = email.strip()
            return email.strip()
    
    return None

def get_forwarded_token() -> Optional[str]:
    """
    Get the forwarded access token for user authentication.
    """
    # Check session state first
    if hasattr(st.session_state, 'auth_headers') and 'access_token' in st.session_state.auth_headers:
        return st.session_state.auth_headers['access_token']
    
    # Check environment variables
    token_env_vars = [
        "HTTP_X_FORWARDED_ACCESS_TOKEN",
        "X_FORWARDED_ACCESS_TOKEN",
        "X-FORWARDED-ACCESS-TOKEN", 
        "DATABRICKS_FORWARD_ACCESS_TOKEN",
        "FORWARDED_ACCESS_TOKEN",
        "ACCESS_TOKEN"
    ]
    
    for env_var in token_env_vars:
        token = os.environ.get(env_var)
        if token and token.strip():
            # Cache in session state
            if not hasattr(st.session_state, 'auth_headers'):
                st.session_state.auth_headers = {}
            st.session_state.auth_headers['access_token'] = token.strip()
            return token.strip()
    
    return None

def get_forwarded_user() -> Optional[str]:
    """
    Get the forwarded user identifier.
    """
    # Check session state first
    if hasattr(st.session_state, 'auth_headers') and 'user' in st.session_state.auth_headers:
        return st.session_state.auth_headers['user']
    
    # Check environment variables
    user_env_vars = [
        "HTTP_X_FORWARDED_USER",
        "X_FORWARDED_USER",
        "X-FORWARDED-USER",
        "DATABRICKS_FORWARD_USER", 
        "FORWARDED_USER",
        "USER_ID",
        "USERNAME"
    ]
    
    for env_var in user_env_vars:
        user = os.environ.get(env_var)
        if user and user.strip():
            # Cache in session state
            if not hasattr(st.session_state, 'auth_headers'):
                st.session_state.auth_headers = {}
            st.session_state.auth_headers['user'] = user.strip()
            return user.strip()
    
    return None

def get_sql_user() -> Optional[str]:
    """
    Get the SQL user from database connection.
    This requires an active database connection.
    """
    try:
        import db
        if hasattr(db, 'current_user') and callable(db.current_user):
            sql_user = db.current_user()
            return sql_user if sql_user and sql_user != "unknown_user" else None
    except Exception:
        pass
    
    return None

def determine_auth_mode() -> str:
    """
    Determine the authentication mode based on available credentials.
    """
    run_as_user = os.getenv("RUN_SQL_AS_USER", "0") == "1"
    has_token = bool(get_forwarded_token())
    
    if run_as_user and has_token:
        return "USER"
    else:
        return "APP"

def get_user_identity() -> Dict[str, Any]:
    """
    Get comprehensive user identity information.
    This is the main function to call for user authentication info.
    
    Returns:
        Dict containing email, sql_user, user_id, auth_mode, and other identity info
    """
    email = get_forwarded_email()
    sql_user = get_sql_user() if os.getenv("DATABRICKS_WAREHOUSE_ID") else None
    forwarded_user = get_forwarded_user()
    auth_mode = determine_auth_mode()
    
    # Determine the primary user ID
    user_id = email or sql_user or forwarded_user or "unknown_user"
    
    return {
        "email": email,
        "sql_user": sql_user, 
        "forwarded_user": forwarded_user,
        "user_id": user_id,
        "auth_mode": auth_mode,
        "has_forwarded_token": bool(get_forwarded_token()),
        "sql_logging_enabled": bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))
    }

def debug_auth_info() -> Dict[str, Any]:
    """
    Get debug information about authentication setup.
    Useful for troubleshooting auth issues.
    """
    debug_info = {
        "environment_variables": {},
        "session_state": {},
        "computed_values": {}
    }
    
    # Check relevant environment variables
    env_vars_to_check = [
        "HTTP_X_FORWARDED_EMAIL",
        "X_FORWARDED_EMAIL", 
        "DATABRICKS_FORWARD_EMAIL",
        "HTTP_X_FORWARDED_ACCESS_TOKEN",
        "X_FORWARDED_ACCESS_TOKEN",
        "DATABRICKS_FORWARD_ACCESS_TOKEN",
        "HTTP_X_FORWARDED_USER",
        "X_FORWARDED_USER",
        "RUN_SQL_AS_USER",
        "DATABRICKS_WAREHOUSE_ID",
        "ENABLE_LOGGING"
    ]
    
    for var in env_vars_to_check:
        value = os.environ.get(var)
        if value:
            # Mask sensitive tokens
            if "TOKEN" in var and len(value) > 10:
                debug_info["environment_variables"][var] = f"{value[:10]}..."
            else:
                debug_info["environment_variables"][var] = value
        else:
            debug_info["environment_variables"][var] = None
    
    # Session state info
    if hasattr(st.session_state, 'auth_headers'):
        debug_info["session_state"]["auth_headers"] = st.session_state.auth_headers
    
    # Computed values
    debug_info["computed_values"] = get_user_identity()
    
    return debug_info

def validate_auth_setup() -> Dict[str, Any]:
    """
    Validate the authentication setup and return status information.
    
    Returns:
        Dict with validation results and recommendations
    """
    user_identity = get_user_identity()
    
    validation = {
        "email_available": bool(user_identity["email"]),
        "sql_user_available": bool(user_identity["sql_user"]),
        "sql_logging_enabled": user_identity["sql_logging_enabled"],
        "auth_mode": user_identity["auth_mode"],
        "recommendations": []
    }
    
    # Generate recommendations
    if not validation["email_available"]:
        validation["recommendations"].append(
            "Email not detected. Ensure X-Forwarded-Email header is set by your proxy/gateway."
        )
    
    if not validation["sql_logging_enabled"]:
        validation["recommendations"].append(
            "SQL logging disabled. Set DATABRICKS_WAREHOUSE_ID to enable conversation history and analytics."
        )
    
    if validation["auth_mode"] == "APP" and os.getenv("RUN_SQL_AS_USER", "0") == "1":
        validation["recommendations"].append(
            "RUN_SQL_AS_USER is enabled but no forwarded token available. Running in APP mode."
        )
    
    return validation