CREATE DATABASE IF NOT EXISTS litecore_tenants;
CREATE DATABASE IF NOT EXISTS litecore_default;

GRANT ALL PRIVILEGES ON litecore_tenants.* TO 'admin'@'%';
GRANT ALL PRIVILEGES ON litecore_default.* TO 'admin'@'%';

FLUSH PRIVILEGES;
