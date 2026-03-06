#!/bin/bash
# web-install.sh - osTicket automated installer
# IDEMPOTENT: Safe to call multiple times - detects existing installations

set -e

echo "🔧 osTicket Web Installer"
echo "========================"

# Check if osTicket is already installed by verifying:
# 1. Config file has OSTINSTALLED=TRUE
# 2. Database has osTicket tables
if grep -q "define('OSTINSTALLED',TRUE)" /var/www/html/include/ost-config.php 2>/dev/null; then
    # Double-check that database tables exist
    TABLE_COUNT=$(mysql -h "${MYSQL_HOST:-mysql}" --ssl=0 -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" \
        -s -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${MYSQL_DATABASE}' AND table_name LIKE '${MYSQL_PREFIX:-ost_}%'" 2>/dev/null || echo "0")
    
    if [ "$TABLE_COUNT" -gt 10 ]; then
        echo "✓ osTicket already fully installed (found $TABLE_COUNT tables) - skipping installation"
        exit 0
    else
        echo "⚠ Config marked as installed but database missing - proceeding with installation"
    fi
fi

echo "⏳ Waiting for database to be ready..."
until mysql -h "${MYSQL_HOST:-mysql}" --ssl=0 -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" "${MYSQL_DATABASE}" -e "SELECT 1" > /dev/null 2>&1; do
    echo "⏳ Database not ready yet..."
    sleep 2
done

echo "✓ Database is ready"

# Ensure /setup directory exists (critical for web installer)
if [ ! -d "/var/www/html/setup" ]; then
    echo "✗ Error: /setup directory not found - installer cannot run"
    exit 1
fi

# Wait for Apache to be fully started
echo "⏳ Waiting for Apache to respond..."
max_attempts=20
attempt=0
while ! curl -sf http://localhost/setup/ > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "✗ Apache not responding after ${max_attempts} attempts"
        exit 1
    fi
    echo "⏳ Waiting for Apache... (attempt $attempt/$max_attempts)"
    sleep 2
done
echo "✓ Apache is responding"

# Step 1: Submit prerequisites check
echo "⏳ Checking prerequisites..."
PREREQ_RESULT=$(curl -sf -X POST http://localhost/setup/install.php \
    -d "s=prereq" \
    -c /tmp/cookies.txt -b /tmp/cookies.txt 2>&1 || echo "")

if echo "$PREREQ_RESULT" | grep -q "error\|failed"; then
    echo "⚠ Prerequisite check had issues: $PREREQ_RESULT"
fi

# Step 2: Config file check  (should pass since entrypoint.sh already created it)
echo "⏳ Verifying configuration file..."
curl -sf -X POST http://localhost/setup/install.php \
    -d "s=config" \
    -c /tmp/cookies.txt -b /tmp/cookies.txt > /dev/null

# Step 3: Run the actual installation with all parameters
echo "⏳ Running installation with environment variables..."
INSTALL_RESULT=$(curl -sf -X POST http://localhost/setup/install.php \
    -c /tmp/cookies.txt -b /tmp/cookies.txt \
    -d "s=install" \
    -d "name=${OST_SITE_NAME:-Support Center}" \
    -d "email=${OST_SITE_EMAIL:-support@example.com}" \
    -d "fname=${OST_ADMIN_FNAME:-Admin}" \
    -d "lname=${OST_ADMIN_LNAME:-User}" \
    -d "admin_email=${OST_ADMIN_EMAIL:-admin@example.com}" \
    -d "username=${OST_ADMIN_USER:-ostadmin}" \
    -d "passwd=${OST_ADMIN_PASS:-Adm1nP@ss!}" \
    -d "passwd2=${OST_ADMIN_PASS:-Adm1nP@ss!}" \
    -d "prefix=${MYSQL_PREFIX:-ost_}" \
    -d "dbhost=${MYSQL_HOST:-mysql}" \
    -d "dbname=${MYSQL_DATABASE:-osticket}" \
    -d "dbuser=${MYSQL_USER:-osticket}" \
    -d "dbpass=${MYSQL_PASSWORD}" \
    -d "lang_id=en_US" 2>&1)

# Check if installation succeeded by looking for OSTINSTALLED=TRUE in config
echo "⏳ Verifying installation..."
sleep 2
if grep -q "define('OSTINSTALLED',TRUE)" /var/www/html/include/ost-config.php 2>/dev/null; then
    echo "✓ Installation completed successfully"
    rm -f /tmp/cookies.txt
    exit 0
else
    echo "✗ Installation failed - OSTINSTALLED not set to TRUE"
    echo "Response excerpt: $(echo "$INSTALL_RESULT" | head -200)"
    rm -f /tmp/cookies.txt
    exit 1
fi

