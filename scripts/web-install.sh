#!/bin/bash
# web-install.sh - osTicket web installer wrapper

set -e

echo "?? osTicket Web Installer"
echo "========================"

# Check if osTicket is already installed
if [ -f "/var/www/html/include/ost-config.php" ]; then
    echo "? osTicket already installed"
    exit 0
fi

echo "? Waiting for database to be ready..."
until mysql -h "${MYSQL_HOST:-db}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" -e "SELECT 1" > /dev/null 2>&1; do
    echo "? Database not ready yet..."
    sleep 2
done

echo "? Database is ready"
echo "? Database connectivity verified"
echo "? osTicket is ready for web-based installation"
echo ""
echo "?? Access the installer at: http://localhost:8080/setup/"
echo "Use the details from .env for database configuration"

