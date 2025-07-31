# Databricks Chat App - Deployment Guide

## Overview

This enhanced Databricks Chat App features an Anthropic-inspired UI with proper left sidebar navigation, fixed email handling, and improved code organization. The application is designed to be modular, maintainable, and production-ready.

## Key Improvements

### 🎨 **UI/UX Enhancements**
- **Anthropic-inspired Design**: Clean, modern interface with proper color scheme and typography
- **Left Sidebar Navigation**: Professional navigation menu replacing tabs
- **Responsive Design**: Works well on desktop and mobile devices
- **Improved Chat Interface**: Better message styling and flow

### 🔧 **Technical Improvements**
- **Fixed Email Bug**: Proper header handling for user authentication
- **Enhanced Error Handling**: Robust database operations with proper logging
- **Modular Architecture**: Separated concerns for better maintainability
- **Better Authentication**: Improved user identity management

### 📊 **Feature Enhancements**
- **Advanced Analytics**: Better usage tracking and visualization
- **Improved History**: Enhanced conversation management
- **Better Settings**: Comprehensive configuration options
- **Status Monitoring**: Real-time system status indicators

## File Structure

```
databricks-chat-app/
├── app.py                 # Main application (enhanced)
├── auth_utils.py          # Authentication utilities (new)
├── ui.py                  # UI components and styling (enhanced)
├── db.py                  # Database operations (enhanced)
├── analytics_utils.py     # Analytics functions (existing)
├── conversations.py       # Conversation management (existing)
├── model_serving_utils.py # Model serving (existing)
├── requirements.txt       # Python dependencies
└── app.yaml              # Databricks App configuration
```

## Configuration

### Environment Variables

#### Required Configuration
```yaml
# Core Model Configuration
SERVING_ENDPOINT: "databricks-claude-sonnet-4"
SERVING_ENDPOINTS_CSV: "databricks-claude-sonnet-4|Claude Sonnet 4,databricks-llama-4-maverick|Llama 4 Maverick"

# Database Configuration (for logging/history)
DATABRICKS_WAREHOUSE_ID: "your-warehouse-id-here"
CATALOG: "shared"
SCHEMA: "app"
ENABLE_LOGGING: "1"
```

#### Optional Configuration
```yaml
# Authentication
RUN_SQL_AS_USER: "0"  # Set to "1" to enable user-based SQL execution

# Chat Configuration
MAX_TURNS: "12"  # Number of conversation turns to send to model

# Cost Tracking (optional)
PRICE_PROMPT_PER_1K: "0.001"
PRICE_COMPLETION_PER_1K: "0.002"
```

### Authentication Setup

The app supports multiple authentication modes:

#### 1. **Forwarded Headers** (Recommended for production)
When deployed behind a proxy/gateway that forwards user information:

```bash
# These headers should be set by your proxy/gateway
X-Forwarded-Email: user@company.com
X-Forwarded-Access-Token: user-access-token
X-Forwarded-User: username
```

#### 2. **Environment Variables** (For development)
```bash
export DATABRICKS_FORWARD_EMAIL="user@company.com"
export DATABRICKS_FORWARD_ACCESS_TOKEN="token"
export DATABRICKS_FORWARD_USER="username"
```

#### 3. **Service Principal** (Default fallback)
Uses the app's service principal credentials automatically.

## Database Setup

### 1. **Create Required Tables**

Run these SQL commands in your Databricks workspace:

```sql
-- Conversations table
CREATE TABLE IF NOT EXISTS shared.app.conversations (
    conversation_id STRING NOT NULL,
    user_id STRING NOT NULL,
    tenant_id STRING DEFAULT 'default',
    title STRING DEFAULT 'New Chat',
    model STRING,
    tools ARRAY<STRING> DEFAULT ARRAY(),
    created_at TIMESTAMP DEFAULT current_timestamp(),
    updated_at TIMESTAMP DEFAULT current_timestamp(),
    meta MAP<STRING, STRING> DEFAULT map(),
    PRIMARY KEY (conversation_id)
) USING DELTA;

-- Messages table
CREATE TABLE IF NOT EXISTS shared.app.messages (
    message_id STRING NOT NULL,
    conversation_id STRING NOT NULL,
    role STRING NOT NULL,
    content STRING,
    tool_invocations ARRAY<STRING> DEFAULT ARRAY(),
    tokens_in INT DEFAULT 0,
    tokens_out INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT current_timestamp(),
    status STRING DEFAULT 'ok',
    PRIMARY KEY (message_id),
    FOREIGN KEY (conversation_id) REFERENCES shared.app.conversations(conversation_id)
) USING DELTA;

-- Usage events table
CREATE TABLE IF NOT EXISTS shared.app.usage_events (
    event_id STRING NOT NULL,
    conversation_id STRING NOT NULL,
    user_id STRING NOT NULL,
    model STRING,
    tokens_in INT DEFAULT 0,
    tokens_out INT DEFAULT 0,
    cost DECIMAL(10,6) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT current_timestamp(),
    meta MAP<STRING, STRING> DEFAULT map(),
    PRIMARY KEY (event_id),
    FOREIGN KEY (conversation_id) REFERENCES shared.app.conversations(conversation_id)
) USING DELTA;
```

### 2. **Grant Permissions**

```sql
-- Grant permissions to your service principal or users
GRANT SELECT, INSERT, UPDATE, DELETE ON shared.app.conversations TO `your-service-principal`;
GRANT SELECT, INSERT, UPDATE, DELETE ON shared.app.messages TO `your-service-principal`;
GRANT SELECT, INSERT, UPDATE, DELETE ON shared.app.usage_events TO `your-service-principal`;
```

## Deployment Steps

### 1. **Prepare Your Environment**

```bash
# Clone or update your code
git clone <your-repo> databricks-chat-app
cd databricks-chat-app

# Install dependencies locally for testing
pip install -r requirements.txt
```

### 2. **Configure app.yaml**

Update your `app.yaml` with your specific values:

```yaml
command: ['streamlit', 'run', 'app.py']
env:
  # Model Configuration
  - name: SERVING_ENDPOINT
    value: "your-primary-endpoint"
  - name: SERVING_ENDPOINTS_CSV
    value: "endpoint1|Display Name 1,endpoint2|Display Name 2"
  
  # Database Configuration
  - name: DATABRICKS_WAREHOUSE_ID
    value: "your-warehouse-id"
  - name: CATALOG
    value: "your-catalog"
  - name: SCHEMA
    value: "your-schema"
  - name: ENABLE_LOGGING
    value: "1"
  
  # Optional Settings
  - name: RUN_SQL_AS_USER
    value: "0"
  - name: MAX_TURNS
    value: "12"
```

### 3. **Deploy to Databricks**

```bash
# Using Databricks CLI
databricks apps create your-app-name

# Or using the Databricks workspace UI
# 1. Go to Apps section
# 2. Create new app
# 3. Upload your files
# 4. Configure environment variables
```

### 4. **Test Deployment**

After deployment, test the following:

1. **Model Connection**: Use the "Test Model" button in the sidebar
2. **Database Connection**: Check the status indicators in the sidebar
3. **Authentication**: Verify user email is displayed correctly
4. **Chat Functionality**: Send a test message and verify response
5. **History**: Create a conversation and check it appears in history
6. **Analytics**: Verify usage metrics are being tracked

## Troubleshooting

### Common Issues

#### 1. **Email Not Detected**
```
Problem: User email shows as "*not available*"
Solution: 
- Check proxy/gateway configuration for X-Forwarded-Email header
- Verify environment variables are set correctly
- Check auth_utils.py debug_auth_info() for troubleshooting
```

#### 2. **Database Connection Failed**
```
Problem: SQL logging shows as "OFF" or errors in logs
Solution:
- Verify DATABRICKS_WAREHOUSE_ID is correct
- Check warehouse permissions
- Ensure tables exist and have proper permissions
- Test connection using db.test_connection()
```

#### 3. **Model Endpoint Not Working**
```
Problem: "Test Model" fails or chat responses error
Solution:
- Verify serving endpoint name is correct
- Check endpoint permissions and status
- Ensure model is deployed and running
- Test endpoint directly in Databricks workspace
```

#### 4. **UI Issues**
```
Problem: Styling not loading or layout broken
Solution:
- Clear browser cache
- Check browser developer console for errors
- Verify CSS injection functions are working
- Test in different browsers
```

### Debug Mode

To enable detailed logging for troubleshooting:

```python
# Add to app.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test authentication
from auth_utils import debug_auth_info
st.json(debug_auth_info())

# Test database
from db import test_connection
st.json(test_connection())
```

## Security Considerations

### 1. **Authentication**
- Use forwarded headers from trusted proxy/gateway
- Never expose access tokens in logs
- Implement proper token validation

### 2. **Database Security**
- Use least privilege access principles
- Regularly rotate service principal credentials
- Monitor database access logs

### 3. **Data Privacy**
- Conversations contain user data - handle appropriately
- Implement data retention policies
- Consider encryption for sensitive conversations

## Performance Optimization

### 1. **Database Performance**
- Index frequently queried columns
- Implement query result caching
- Use OPTIMIZE and VACUUM commands regularly

### 2. **Model Performance** 
- Monitor token usage and costs
- Implement conversation context limits
- Cache frequently requested data

### 3. **UI Performance**
- Minimize CSS size and complexity
- Use efficient Streamlit components
- Implement proper error boundaries

## Monitoring and Maintenance

### 1. **Health Checks**
- Monitor model endpoint availability
- Check database connection status
- Track error rates and response times

### 2. **Usage Analytics**
- Monitor token consumption and costs
- Track user engagement metrics
- Analyze conversation patterns

### 3. **Regular Maintenance**
- Update dependencies regularly
- Review and optimize database queries
- Clean up old conversation data as needed

## Support and Contributing

For issues, feature requests, or contributions:
1. Check the troubleshooting section above
2. Review application logs for error details
3. Test individual components using debug functions
4. Create detailed issue reports with logs and configuration

The application is designed to be maintainable and extensible. The modular architecture allows for easy customization and enhancement of individual components.