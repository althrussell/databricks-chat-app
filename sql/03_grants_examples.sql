-- Example grants (adjust principals for your workspace)
USE CATALOG shared;

-- If logging uses the App identity (RUN_SQL_AS_USER=0), grant the App/SP principal:
-- REPLACE '<app-principal>' with your App service principal or group
GRANT USAGE ON CATALOG shared TO `<app-principal>`;
GRANT USE SCHEMA, CREATE, SELECT, INSERT, UPDATE ON SCHEMA shared.app TO `<app-principal>`;

-- If using OBO (RUN_SQL_AS_USER=1), end-users need rights themselves:
-- REPLACE '<allowed-group>' with a workspace group
GRANT USAGE ON CATALOG shared TO `<allowed-group>`;
GRANT USE SCHEMA, SELECT, INSERT, UPDATE ON SCHEMA shared.app TO `<allowed-group>`;

-- Volume access (for future uploads/exports)
GRANT READ VOLUME, WRITE VOLUME ON VOLUME shared.app.user_files TO `<app-principal>`;
